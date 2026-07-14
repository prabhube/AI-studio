"""
Request Timing Middleware.

Measures wall-clock time for every HTTP request and adds the result to:
  - Response header X-Process-Time-Ms  (always, for client observability)
  - Structured log (always, for server-side observability)

Design decisions:
  - Uses time.perf_counter() for sub-millisecond accuracy.
  - Skips the /health endpoint to avoid polluting logs with monitoring noise.
  - Emits a WARNING log for requests that exceed SLOW_REQUEST_THRESHOLD_MS,
    allowing SREs to detect performance regressions without querying logs.
  - The header value is in milliseconds (not seconds) because that is what
    browser developer tools and most monitoring tools expect.
"""

from __future__ import annotations

import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)

# Requests longer than this (ms) emit a WARNING-level log entry.
_SLOW_REQUEST_THRESHOLD_MS: float = 500.0

# Paths that are excluded from timing logs (high-frequency health checks).
_SKIP_LOG_PATHS: frozenset[str] = frozenset({"/api/v1/health"})


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Add X-Process-Time-Ms to every response and log request duration.

    Execution order in the middleware stack:
        RequestIDMiddleware  →  TimingMiddleware  →  route handler
    Timing starts AFTER the request ID is assigned so the ID appears
    in the slow-request log entry.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()

        response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start) * 1000
        elapsed_ms_rounded = round(elapsed_ms, 2)

        # Add timing header to every response
        response.headers["X-Process-Time-Ms"] = str(elapsed_ms_rounded)

        # Skip log for high-frequency paths (health checks)
        if request.url.path in _SKIP_LOG_PATHS:
            return response

        log_fn = (
            logger.warning
            if elapsed_ms >= _SLOW_REQUEST_THRESHOLD_MS
            else logger.info
        )

        log_fn(
            "http_request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=elapsed_ms_rounded,
            slow=elapsed_ms >= _SLOW_REQUEST_THRESHOLD_MS,
        )

        return response
