"""
Async Redis client factory and FastAPI dependency.

Design decisions:
  - Single client instance created on first call (singleton pattern).
  - Exponential backoff retry for transient connection failures at startup.
    Redis may not be available immediately when Docker containers start.
  - health_check_interval keeps idle connections alive with periodic PINGs,
    preventing silent disconnections in long-idle development environments.
  - All operations wrap exceptions in CacheError so callers don't need
    to import redis exceptions directly.
  - Separate get_redis() generator for FastAPI dependency injection.
    The generator yields the shared client (no per-request connection).
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.config import get_settings
from app.core.exceptions import CacheError
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis_client: Redis | None = None

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _create_client_with_retry(
    url: str,
    max_attempts: int,
    *,
    connect_timeout: int,
    socket_timeout: int,
    max_connections: int,
    health_check_interval: int,
    retry_on_timeout: bool,
) -> Redis:
    """
    Create a Redis client and verify connectivity with exponential backoff.

    Args:
        url:                   Redis connection URL.
        max_attempts:          Maximum number of connection attempts.
        connect_timeout:       Seconds to wait for the TCP connection.
        socket_timeout:        Seconds to wait for a socket operation.
        max_connections:       Maximum connections in the pool.
        health_check_interval: Seconds between idle health pings.
        retry_on_timeout:      Retry commands that time out.

    Returns:
        A connected, verified Redis client.

    Raises:
        CacheError: After all retry attempts are exhausted.
    """
    client: Redis = aioredis.from_url(
        url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=connect_timeout,
        socket_timeout=socket_timeout,
        max_connections=max_connections,
        retry_on_timeout=retry_on_timeout,
        health_check_interval=health_check_interval,
    )

    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            await client.ping()
            logger.info("redis_connected", attempt=attempt)
            return client
        except (RedisConnectionError, RedisTimeoutError, OSError) as exc:
            last_exc = exc
            if attempt == max_attempts:
                break
            # Exponential backoff: 1s, 2s, 4s …
            wait = 2 ** (attempt - 1)
            logger.warning(
                "redis_connection_attempt_failed",
                attempt=attempt,
                max_attempts=max_attempts,
                retry_in_seconds=wait,
                error=str(exc),
            )
            await asyncio.sleep(wait)

    await client.aclose()
    raise CacheError(
        f"Redis connection failed after {max_attempts} attempts: {last_exc}"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_redis_client() -> Redis:
    """
    Return the singleton async Redis client.

    Creates and verifies the connection on the first call,
    then returns the cached client on subsequent calls.

    Raises:
        CacheError: If the connection cannot be established.
    """
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    settings = get_settings()
    r = settings.redis

    _redis_client = await _create_client_with_retry(
        url=r.url,
        max_attempts=r.retry_max_attempts,
        connect_timeout=r.socket_connect_timeout,
        socket_timeout=r.socket_timeout,
        max_connections=r.max_connections,
        health_check_interval=r.health_check_interval,
        retry_on_timeout=r.retry_on_timeout,
    )

    return _redis_client


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    FastAPI dependency that yields the shared Redis client.

    Note: This yields the singleton client, not a dedicated connection.
    Redis clients are thread/coroutine safe and manage their own pool.

    Usage in route handlers:
        @router.get("/example")
        async def example(redis: Redis = Depends(get_redis)):
            value = await redis.get("key")
    """
    client = await get_redis_client()
    yield client


async def check_redis_connection() -> float:
    """
    Verify Redis is reachable by sending a PING command.

    Returns the round-trip time in milliseconds.

    Raises:
        CacheError: If the PING fails.
    """
    try:
        client = await get_redis_client()
        start = time.perf_counter()
        await client.ping()
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.debug("redis_health_check_ok", elapsed_ms=round(elapsed_ms, 2))
        return elapsed_ms
    except (RedisConnectionError, RedisTimeoutError, CacheError) as exc:
        raise CacheError(f"Redis health check failed: {exc}") from exc


async def close_redis_client() -> None:
    """
    Close the Redis connection pool.

    Call during application shutdown. Safe to call even if the client
    was never initialised.
    """
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception as exc:
            logger.warning("redis_close_error", error=str(exc))
        finally:
            _redis_client = None
            logger.info("redis_connection_closed")
