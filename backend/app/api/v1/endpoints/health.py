"""
Health check endpoint.

Design decisions:
  - Returns HTTP 200 even when services are degraded, so that load
    balancers do not take the API offline when only Redis is down.
    The 'status' field in the body conveys the real state.
  - Returns HTTP 503 only when the database (required for core operation)
    is completely unreachable.
  - Measures and reports latency for each dependency so SREs can spot
    performance degradation before it becomes an outage.
  - Checks available disk space on the media directory — AI generation
    will fail silently if disk is full.
  - The endpoint itself is exempt from rate limiting (it's called
    frequently by Docker and monitoring systems).
"""

from __future__ import annotations

import os
import shutil
import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import CacheError, DatabaseError
from app.core.logging import get_logger
from app.db.redis_client import check_redis_connection
from app.db.session import check_database_connection
from app.schemas.common import HealthCheckResponse, ServiceStatus

router = APIRouter()
logger = get_logger(__name__)

# Timestamp of when the process started — used to calculate uptime.
_PROCESS_START = time.monotonic()


def _check_disk(path: str) -> dict:
    """
    Return disk usage statistics for the given path.

    Returns a dict with total_gb, used_gb, free_gb, and percent_used.
    Returns an error dict if the path doesn't exist.
    """
    try:
        usage = shutil.disk_usage(path)
        gb = 1024 ** 3
        return {
            "path": path,
            "total_gb": round(usage.total / gb, 2),
            "used_gb": round(usage.used / gb, 2),
            "free_gb": round(usage.free / gb, 2),
            "percent_used": round((usage.used / usage.total) * 100, 1),
        }
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return {"path": path, "error": str(exc)}


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Application health check",
    description=(
        "Returns the operational status of the application and all "
        "infrastructure dependencies. Used by Docker, load balancers, "
        "and monitoring systems."
    ),
    tags=["Health"],
    include_in_schema=True,
)
async def health_check() -> JSONResponse:
    """
    Check the health of all application dependencies.

    HTTP status codes:
      - 200: Application is fully healthy or degraded but operational.
      - 503: Database is unreachable; application cannot serve requests.
    """
    settings = get_settings()
    services: dict[str, ServiceStatus] = {}
    db_healthy = False

    # ------------------------------------------------------------------
    # PostgreSQL
    # ------------------------------------------------------------------
    try:
        latency_ms = await check_database_connection()
        services["postgres"] = ServiceStatus(
            status="ok", latency_ms=round(latency_ms, 2)
        )
        db_healthy = True
    except DatabaseError as exc:
        services["postgres"] = ServiceStatus(
            status="error", detail=type(exc).__name__
        )
        logger.error("health_check_postgres_failed", error=str(exc))

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    try:
        latency_ms = await check_redis_connection()
        services["redis"] = ServiceStatus(
            status="ok", latency_ms=round(latency_ms, 2)
        )
    except CacheError as exc:
        services["redis"] = ServiceStatus(
            status="error", detail=type(exc).__name__
        )
        logger.warning("health_check_redis_failed", error=str(exc))

    # ------------------------------------------------------------------
    # Disk space
    # ------------------------------------------------------------------
    media_path = settings.media_root
    disk_info = _check_disk(media_path)

    # Warn if disk is more than 90% full
    if isinstance(disk_info.get("percent_used"), float):
        if disk_info["percent_used"] > 90:
            logger.warning(
                "disk_space_critical",
                percent_used=disk_info["percent_used"],
                free_gb=disk_info["free_gb"],
            )

    # ------------------------------------------------------------------
    # Overall status
    # ------------------------------------------------------------------
    all_ok = all(s.status == "ok" for s in services.values())
    overall = "ok" if all_ok else "degraded"

    body = HealthCheckResponse(
        status=overall,
        version=settings.app_version,
        environment=settings.app_env,
        uptime_seconds=round(time.monotonic() - _PROCESS_START, 1),
        services=services,
        disk=disk_info,
    )

    # Return 503 only when the database is completely down —
    # that makes the app unable to serve any request at all.
    http_status = 200 if db_healthy else 503

    return JSONResponse(
        content=body.model_dump(),
        status_code=http_status,
    )
