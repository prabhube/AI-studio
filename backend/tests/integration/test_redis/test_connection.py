"""
Integration tests for Redis connectivity.

These tests require a running Redis instance and are skipped
in the standard unit test run. Run explicitly with:

    pytest tests/integration/ -v --run-integration

Or set INTEGRATION_TESTS=1 in the environment.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("INTEGRATION_TESTS"),
    reason="Set INTEGRATION_TESTS=1 to run integration tests.",
)


@pytest.mark.asyncio
class TestRedisConnection:
    """Verify the application can connect to Redis."""

    async def test_redis_ping_succeeds(self):
        """check_redis_connection() should return a positive latency."""
        from app.db.redis_client import check_redis_connection

        latency_ms = await check_redis_connection()
        assert isinstance(latency_ms, float)
        assert latency_ms > 0

    async def test_redis_set_and_get(self):
        """A basic set/get round-trip should succeed."""
        from app.db.redis_client import get_redis_client

        client = await get_redis_client()
        await client.set("test_key", "test_value", ex=60)
        value = await client.get("test_key")
        assert value == "test_value"
        await client.delete("test_key")

    async def test_celery_task_routing(self):
        """
        Verify Celery can connect to Redis as its broker.

        This test ensures the REDIS_URL in settings matches the
        Celery broker URL, and that Celery can inspect connected workers.
        """
        pytest.skip(
            "Implement: instantiate Celery app, call inspect().ping(), verify response."
        )
