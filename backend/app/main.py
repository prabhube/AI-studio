"""
Prabhu AI Studio — FastAPI application entry point.

Wiring:
  - Lifespan context manager handles all startup / shutdown logic.
  - Application factory (create_application) returns a configured FastAPI
    instance; this pattern makes it easy to create test instances.
  - Middleware is added in reverse execution order (last added = first run).
    Correct order from outermost to innermost:
        1. RequestIDMiddleware   — assigns X-Request-ID first
        2. TimingMiddleware      — starts the clock after ID is bound
        3. CORSMiddleware        — handles preflight before any logic
        4. SlowAPIMiddleware     — rate limiting
  - Exception handlers are registered before routers.
  - OpenAPI docs are disabled in production.
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.redis_client import close_redis_client, get_redis_client
from app.db.session import check_database_connection, dispose_engine, get_engine
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.timing_middleware import TimingMiddleware
from app.utils.exception_handlers import register_exception_handlers

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Media directory setup
# ---------------------------------------------------------------------------


def _create_media_directories(media_root: Path) -> None:
    """
    Create all required media subdirectories on startup.

    This ensures AI generation tasks have a valid write target
    even when the volume is freshly mounted.
    """
    subdirs = ["images", "videos", "audio", "transcripts", "thumbnails", "temp"]
    for subdir in subdirs:
        path = media_root / subdir
        path.mkdir(parents=True, exist_ok=True)
    logger.info("media_directories_ready", root=str(media_root))


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Startup sequence (order matters):
      1. Configure structured logging first — all subsequent steps log.
      2. Validate media directories exist and are writable.
      3. Warm the database connection pool — raises on hard failure.
      4. Test Redis — logs a warning on failure (non-fatal: some endpoints
         degrade gracefully without Redis).

    Shutdown sequence:
      1. Dispose database engine — closes all pooled connections.
      2. Close Redis client — flushes any pending pipeline commands.
    """
    settings = get_settings()

    # Step 1 — Configure logging before anything else
    configure_logging(debug=settings.app_debug, environment=settings.app_env)

    logger.info(
        "application_starting",
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        python=sys.version.split()[0],
    )

    # Step 2 — Media directories
    try:
        _create_media_directories(settings.media_root_path)
    except OSError as exc:
        logger.warning("media_directory_setup_failed", error=str(exc))

    # Step 3 — Database
    try:
        get_engine()  # creates pool
        latency_ms = await check_database_connection()
        logger.info("database_ready", latency_ms=round(latency_ms, 2))
    except Exception as exc:
        logger.critical(
            "database_connection_failed",
            error=str(exc),
            hint="Check POSTGRES_* env vars and that PostgreSQL is running.",
        )
        # Hard failure — application cannot function without the database.
        # Raising here causes uvicorn to exit with a non-zero exit code,
        # which Docker Compose will treat as an unhealthy service.
        raise

    # Step 4 — Redis (non-fatal)
    try:
        await get_redis_client()
        logger.info("redis_ready")
    except Exception as exc:
        logger.warning(
            "redis_unavailable_on_startup",
            error=str(exc),
            hint="Rate limiting and task queuing may be degraded.",
        )

    logger.info("application_started")

    yield  # ← application is running; requests are being served

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------
    logger.info("application_shutting_down")

    await dispose_engine()
    await close_redis_client()

    logger.info("application_stopped")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_application() -> FastAPI:
    """
    Return a fully configured FastAPI application instance.

    This factory function is called once at module import time to create
    the global `app` object, and also by the test suite to create isolated
    instances with patched settings.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "**Prabhu AI Studio** — Local-first AI video generation platform.\n\n"
            "Generate complete videos from text prompts using open-source AI models "
            "running entirely on your own hardware.\n\n"
            "All AI processing is local: no data leaves your machine."
        ),
        contact={
            "name": "Prabhu AI Studio",
            "url": "https://github.com/prabhu-ai-studio",
        },
        # Only expose docs in non-production environments
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        openapi_url="/api/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # Rate limiting (SlowAPI)
    # ------------------------------------------------------------------
    limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ------------------------------------------------------------------
    # Exception handlers
    # Must be registered BEFORE routers so they catch router-level errors.
    # ------------------------------------------------------------------
    register_exception_handlers(app)

    # ------------------------------------------------------------------
    # Middleware stack
    # FastAPI applies middleware in reverse registration order.
    # To execute in this order:
    #   RequestID → Timing → CORS → RateLimit → route handler
    # Register them in this order (last registered = outermost = runs first):
    #   SlowAPI, CORS, Timing, RequestID
    # ------------------------------------------------------------------
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
    )

    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # ------------------------------------------------------------------
    # API routers
    # ------------------------------------------------------------------
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_application()
