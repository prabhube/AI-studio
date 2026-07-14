"""
Pytest configuration and shared fixtures for all test suites.

Architecture:
  - Tests use an in-memory SQLite database (aiosqlite driver) instead
    of PostgreSQL. This keeps tests fast and dependency-free.
  - The test engine is created once per session; tables are created once
    and dropped at session teardown.
  - Each test gets a fresh DB session that is rolled back at the end,
    keeping tests fully isolated without recreating tables.
  - The FastAPI app is created fresh per test with the DB dependency
    overridden to inject the test session.
  - Redis is mocked via AsyncMock — unit and API tests do not need a
    real Redis instance. Integration tests can override this fixture.
  - Auth fixtures (test_user, superuser, auth_headers) are available
    for endpoint tests but are NOT required for infrastructure tests.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.db.base import Base
from app.db.redis_client import get_redis
from app.db.session import get_db_session
from app.main import create_application

# ---------------------------------------------------------------------------
# Configuration — use in-memory SQLite for speed; swap for real Postgres in CI
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ---------------------------------------------------------------------------
# Event loop
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop():
    """Provide a single event loop for the entire test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create an async SQLite engine with all application tables.

    SQLite requires check_same_thread=False when used in an async context
    across multiple coroutines. The engine is shared for the full session
    to avoid recreating tables between tests.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an isolated database session for one test.

    The session is rolled back at the end of every test, so each test
    starts with a clean slate without recreating the schema.
    """
    factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with factory() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Redis mock
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_redis() -> AsyncMock:
    """
    Return a fully-mocked async Redis client.

    Covers the most common operations. Tests that exercise specific Redis
    behaviour should configure return values directly on this fixture.

    Example:
        async def test_cache_hit(mock_redis):
            mock_redis.get.return_value = '{"cached": true}'
            ...
    """
    mock = AsyncMock()
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = 0
    mock.expire.return_value = True
    mock.ttl.return_value = -1
    mock.incr.return_value = 1
    mock.lpush.return_value = 1
    mock.lrange.return_value = []
    mock.pipeline.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
    mock.pipeline.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------


@pytest.fixture
def app(db_session: AsyncSession, mock_redis: AsyncMock) -> FastAPI:
    """
    Return a test FastAPI application with overridden infrastructure deps.

    - DB session → injected test session (rolls back after each test)
    - Redis client → AsyncMock (no real Redis required)
    """
    application = create_application()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def _override_get_redis() -> AsyncGenerator[AsyncMock, None]:
        yield mock_redis

    application.dependency_overrides[get_db_session] = _override_get_db
    application.dependency_overrides[get_redis] = _override_get_redis

    return application


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Return an async HTTP test client pointing at the test application."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Auth fixtures (used by endpoint tests; ignored by infrastructure tests)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """
    Create and persist a standard test user.

    Import User and hash_password lazily so tests that don't use auth
    don't pay the bcrypt import cost.
    """
    from app.core.security import hash_password
    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        username="testuser",
        hashed_password=hash_password("TestPass1!"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def superuser(db_session: AsyncSession):
    """Create and persist a superuser for admin-protected endpoint tests."""
    from app.core.security import hash_password
    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        username="admin",
        hashed_password=hash_password("AdminPass1!"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user) -> dict[str, str]:
    """Return Bearer token headers for the test user."""
    from app.core.security import create_access_token

    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def superuser_auth_headers(superuser) -> dict[str, str]:
    """Return Bearer token headers for the superuser."""
    from app.core.security import create_access_token

    token = create_access_token(subject=str(superuser.id))
    return {"Authorization": f"Bearer {token}"}
