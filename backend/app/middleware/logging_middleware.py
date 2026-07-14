"""
HTTP Access Logging Middleware.

WHY this file exists:
    Logs every request and response with:
    - HTTP method and path
    - Response status code
    - Request duration in milliseconds
    - Request ID (from RequestIDMiddleware)

    This gives developers a complete picture of API traffic without
    relying on uvicorn's default access logs (which lack context).

    Output (development):
        [INFO] GET /api/v1/users/me 200 OK 12ms request_id=abc-123

Implementation: Phase 1 (lightweight — no AI dependencies).
"""

import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)


class AccessLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log every request with timing information.

    Skips /health endpoint to avoid log noise from monitoring
    systems that poll health checks every 10 seconds.
    """

    SKIP_PATHS = {"/api/v1/health"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response
