"""
Integration tests for database connectivity and migrations.

These tests require a running PostgreSQL instance and are skipped
in the standard unit test run. Run explicitly with:

    pytest tests/integration/ -v --run-integration

Or set INTEGRATION_TESTS=1 in the environment.
"""

from __future__ import annotations

import os

import pytest
import pytest_asyncio

pytestmark = pytest.mark.skipif(
    not os.getenv("INTEGRATION_TESTS"),
    reason="Set INTEGRATION_TESTS=1 to run integration tests.",
)


@pytest.mark.asyncio
class TestDatabaseConnection:
    """Verify the application can connect to PostgreSQL."""

    async def test_postgres_connection_succeeds(self):
        """check_database_connection() should return a positive latency."""
        from app.db.session import check_database_connection

        latency_ms = await check_database_connection()
        assert isinstance(latency_ms, float)
        assert latency_ms > 0

    async def test_database_select_returns_one(self):
        """A raw SELECT 1 should succeed and return a result."""
        from sqlalchemy import text

        from app.db.session import get_engine

        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row is not None
            assert row[0] == 1

    async def test_migrations_apply_cleanly(self):
        """
        Alembic should be able to run all migrations up to head
        against the configured database.

        This test verifies migration scripts are syntactically valid
        and logically compatible with the current schema.
        """
        pytest.skip("Implement: run alembic upgrade head, verify no errors.")


@pytest.mark.asyncio
class TestSessionBehaviour:
    """Verify session rollback on error."""

    async def test_rollback_on_exception_does_not_corrupt_pool(self):
        """After a rollback, the connection must be clean and reusable."""
        from sqlalchemy import text

        from app.db.session import get_session_factory

        factory = get_session_factory()
        async with factory() as session:
            try:
                await session.execute(text("SELECT 1 / 0"))
            except Exception:
                await session.rollback()

        # If pool was corrupted, the next query would fail
        async with factory() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
