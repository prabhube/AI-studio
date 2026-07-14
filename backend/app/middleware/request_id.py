"""
Request ID Middleware.

Assigns a unique UUID to every HTTP request and propagates it through:
  - structlog contextvars (appears in every log line for this request)
  - X-Request-ID response header (returned to the client)

Design decisions:
  - If the client sends an X-Request-ID header, that value is used.
    This allows distributed tracing across services or from a gateway.
  - If no header is present, a new UUID4 is generated.
  - structlog.contextvars is cleared at the start of each request to
    prevent context leaking between requests in the same worker.
  - The request ID is also available at request.state.request_id so
    other middleware and dependencies can read it without an import.
"""

from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Inject and propagate a unique X-Request-ID on every request.

    Must be the FIRST middleware in the stack so that subsequent
    middleware and all route handlers see the request ID in logs.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Accept existing ID from client/gateway, or generate a new one.
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Attach to request state for use by dependencies
        request.state.request_id = request_id

        # Bind to structlog contextvars — automatically included in all logs
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
