"""
Async SQLAlchemy session factory and FastAPI dependency.

Design decisions:
  - Engine is a module-level singleton created once on first call.
    This keeps connection pool resources alive across all requests.
  - pool_pre_ping=True sends a lightweight SELECT 1 before handing
    a connection to the application, preventing "connection closed"
    errors after PostgreSQL restarts or idle timeouts.
  - pool_recycle avoids holding connections that PostgreSQL has timed
    out on its side (default server-side timeout is often 10 minutes).
  - Event listeners capture slow queries and pool events for observability.
  - get_db_session() rolls back on any exception before re-raising,
    ensuring dirty sessions are never silently reused.
"""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import Pool

from app.core.config import get_settings
from app.core.exceptions import DatabaseError
from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None

# Threshold (seconds) above which a query is logged as a slow query warning.
_SLOW_QUERY_THRESHOLD: float = 1.0


# ---------------------------------------------------------------------------
# Event listeners — attached once when the engine is created
# ---------------------------------------------------------------------------


def _register_pool_events(engine: AsyncEngine) -> None:
    """
    Attach SQLAlchemy pool-level event listeners for observability.

    These fire on the synchronous Pool, not on async sessions, so
    the handlers are ordinary (not async) functions.
    """
    sync_pool: Pool = engine.sync_engine.pool

    @event.listens_for(sync_pool, "connect")
    def on_connect(dbapi_conn, connection_record):  # type: ignore[no-untyped-def]
        logger.debug("db_pool_connect", thread_ident=connection_record.thread_ident)

    @event.listens_for(sync_pool, "checkout")
    def on_checkout(dbapi_conn, connection_record, connection_proxy):  # type: ignore[no-untyped-def]
        logger.debug("db_pool_checkout")

    @event.listens_for(sync_pool, "checkin")
    def on_checkin(dbapi_conn, connection_record):  # type: ignore[no-untyped-def]
        logger.debug("db_pool_checkin")

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def before_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore[no-untyped-def]
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())

    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def after_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore[no-untyped-def]
        start_times: list[float] = conn.info.get("query_start_time", [])
        if not start_times:
            return
        elapsed = time.perf_counter() - start_times.pop()
        if elapsed >= _SLOW_QUERY_THRESHOLD:
            # Trim the statement for the log — avoid logging full data
            short_stmt = statement.strip()[:200].replace("\n", " ")
            logger.warning(
                "slow_query_detected",
                elapsed_seconds=round(elapsed, 4),
                statement_preview=short_stmt,
            )


# ---------------------------------------------------------------------------
# Engine and session factory
# ---------------------------------------------------------------------------


def get_engine() -> AsyncEngine:
    """
    Return the singleton async SQLAlchemy engine.

    Creates the engine on first call, attaches event listeners, and
    caches it for the lifetime of the process.

    This function is safe to call multiple times — only one engine
    is ever created.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        db = settings.database

        _engine = create_async_engine(
            db.url,
            pool_size=db.pool_size,
            max_overflow=db.max_overflow,
            pool_timeout=db.pool_timeout,
            pool_recycle=db.pool_recycle,
            echo=db.echo,
            pool_pre_ping=True,
        )

        _register_pool_events(_engine)
        logger.info("database_engine_created", dsn=db.safe_url)

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Return the singleton async session factory.

    expire_on_commit=False prevents SQLAlchemy from expiring attributes
    after commit, so models can be safely read after the transaction ends
    (important for async code where lazy-loading is not possible).
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a database session scoped to the current HTTP request.

    Behaviour:
      - On success: commits the transaction.
      - On any exception: rolls back, then re-raises unchanged.
      - Always: closes the session (returns connection to pool).

    Usage in route handlers:
        @router.get("/example")
        async def example(session: AsyncSession = Depends(get_db_session)):
            ...
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as exc:
            await session.rollback()
            logger.error("database_transaction_error", error=str(exc))
            raise DatabaseError(f"Database operation failed: {type(exc).__name__}") from exc
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Lifecycle helpers
# ---------------------------------------------------------------------------


async def check_database_connection() -> float:
    """
    Verify the database is reachable by running a SELECT 1.

    Returns the round-trip time in milliseconds.

    Raises:
        DatabaseError: If the connection fails.
    """
    engine = get_engine()
    start = time.perf_counter()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.debug("database_health_check_ok", elapsed_ms=round(elapsed_ms, 2))
        return elapsed_ms
    except (OperationalError, SQLAlchemyError) as exc:
        raise DatabaseError(f"Database health check failed: {exc}") from exc


async def dispose_engine() -> None:
    """
    Close all database connections and dispose of the engine.

    Call during application shutdown. After this, get_engine() will
    create a fresh engine on the next call.
    """
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("database_engine_disposed")
