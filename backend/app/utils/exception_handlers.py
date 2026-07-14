"""
Global FastAPI exception handlers.

Design decisions:
  - Every handler returns the same ErrorResponse envelope so the frontend
    can handle errors with one code path.
  - In production, internal error details (stack traces, SQL errors, etc.)
    are NEVER sent to the client. They are logged server-side only.
  - The request_id (from X-Request-ID header) is echoed back in every
    error response so developers can correlate client errors with server logs.
  - Domain exceptions map to HTTP status codes here, not in the services.
    Services only raise domain exceptions; this layer translates them.
  - The 'unhandled_exception_handler' is a safety net. If it triggers
    frequently, it means a domain exception is missing for a real error case.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import (
    AIProviderError,
    AuthenticationError,
    AuthorizationError,
    CacheError,
    DatabaseError,
    InvalidInputError,
    PrabhuBaseException,
    ProviderNotConfiguredError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    TokenExpiredError,
    TokenInvalidError,
    ValidationError,
)
from app.schemas.common import ErrorDetail, ErrorResponse

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _request_id(request: Request) -> str | None:
    """Extract X-Request-ID from the request headers."""
    return request.headers.get("X-Request-ID")


def _json_error(
    status_code: int,
    error: str,
    *,
    request: Request,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    """Build a standardised JSON error response."""
    body = ErrorResponse(
        error=error,
        details=details,
        request_id=_request_id(request),
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


def _safe_detail(exc: Exception, *, public: bool = False) -> str:
    """
    Return a user-safe error detail string.

    In production, only pre-approved public messages are returned.
    In development, the full exception string is returned for easier debugging.
    """
    settings = get_settings()
    if settings.is_production and not public:
        return "An internal error occurred."
    return str(exc)


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all global exception handlers on the FastAPI application.

    Call this once in the application factory before adding routers.
    Order matters: more specific exceptions must be registered BEFORE
    their base classes, because FastAPI checks handlers in registration order.
    """

    # ------------------------------------------------------------------
    # Pydantic / FastAPI request validation (422)
    # ------------------------------------------------------------------
    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            ErrorDetail(
                field=" → ".join(str(loc) for loc in err["loc"] if loc != "body"),
                message=err["msg"],
            )
            for err in exc.errors()
        ]
        logger.info(
            "request_validation_error",
            path=request.url.path,
            error_count=len(details),
        )
        return _json_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Request validation failed.",
            request=request,
            details=details,
        )

    # ------------------------------------------------------------------
    # Token errors — 401
    # ------------------------------------------------------------------
    @app.exception_handler(TokenExpiredError)
    async def handle_token_expired(
        request: Request, exc: TokenExpiredError
    ) -> JSONResponse:
        response = _json_error(
            status.HTTP_401_UNAUTHORIZED,
            exc.message,
            request=request,
        )
        response.headers["WWW-Authenticate"] = "Bearer"
        return response

    @app.exception_handler(TokenInvalidError)
    async def handle_token_invalid(
        request: Request, exc: TokenInvalidError
    ) -> JSONResponse:
        response = _json_error(
            status.HTTP_401_UNAUTHORIZED,
            exc.message,
            request=request,
        )
        response.headers["WWW-Authenticate"] = "Bearer"
        return response

    # ------------------------------------------------------------------
    # Authentication — 401
    # ------------------------------------------------------------------
    @app.exception_handler(AuthenticationError)
    async def handle_authentication(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        response = _json_error(
            status.HTTP_401_UNAUTHORIZED,
            exc.message,
            request=request,
        )
        response.headers["WWW-Authenticate"] = "Bearer"
        return response

    # ------------------------------------------------------------------
    # Authorization — 403
    # ------------------------------------------------------------------
    @app.exception_handler(AuthorizationError)
    async def handle_authorization(
        request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        return _json_error(
            status.HTTP_403_FORBIDDEN,
            exc.message,
            request=request,
        )

    # ------------------------------------------------------------------
    # Resource not found — 404
    # ------------------------------------------------------------------
    @app.exception_handler(ResourceNotFoundError)
    async def handle_not_found(
        request: Request, exc: ResourceNotFoundError
    ) -> JSONResponse:
        return _json_error(
            status.HTTP_404_NOT_FOUND,
            exc.message,
            request=request,
        )

    # ------------------------------------------------------------------
    # Conflict — 409
    # ------------------------------------------------------------------
    @app.exception_handler(ResourceAlreadyExistsError)
    async def handle_conflict(
        request: Request, exc: ResourceAlreadyExistsError
    ) -> JSONResponse:
        return _json_error(
            status.HTTP_409_CONFLICT,
            exc.message,
            request=request,
        )

    # ------------------------------------------------------------------
    # Domain validation — 400
    # ------------------------------------------------------------------
    @app.exception_handler(InvalidInputError)
    async def handle_invalid_input(
        request: Request, exc: InvalidInputError
    ) -> JSONResponse:
        return _json_error(
            status.HTTP_400_BAD_REQUEST,
            exc.message,
            request=request,
        )

    @app.exception_handler(ValidationError)
    async def handle_domain_validation(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        return _json_error(
            status.HTTP_400_BAD_REQUEST,
            exc.message,
            request=request,
        )

    # ------------------------------------------------------------------
    # AI provider not configured — 503
    # ------------------------------------------------------------------
    @app.exception_handler(ProviderNotConfiguredError)
    async def handle_provider_not_configured(
        request: Request, exc: ProviderNotConfiguredError
    ) -> JSONResponse:
        return _json_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            exc.message,
            request=request,
        )

    # ------------------------------------------------------------------
    # AI provider runtime errors — 502
    # ------------------------------------------------------------------
    @app.exception_handler(AIProviderError)
    async def handle_ai_provider_error(
        request: Request, exc: AIProviderError
    ) -> JSONResponse:
        logger.error(
            "ai_provider_error",
            path=request.url.path,
            error=str(exc),
            provider=type(exc).__name__,
        )
        return _json_error(
            status.HTTP_502_BAD_GATEWAY,
            _safe_detail(exc, public=False),
            request=request,
        )

    # ------------------------------------------------------------------
    # Database errors — 503
    # ------------------------------------------------------------------
    @app.exception_handler(DatabaseError)
    async def handle_database_error(
        request: Request, exc: DatabaseError
    ) -> JSONResponse:
        logger.error(
            "database_error",
            path=request.url.path,
            error=str(exc),
        )
        return _json_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "A database error occurred. Please try again shortly.",
            request=request,
        )

    # ------------------------------------------------------------------
    # Cache errors — 503
    # ------------------------------------------------------------------
    @app.exception_handler(CacheError)
    async def handle_cache_error(
        request: Request, exc: CacheError
    ) -> JSONResponse:
        logger.warning(
            "cache_error",
            path=request.url.path,
            error=str(exc),
        )
        return _json_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "A cache error occurred. Please try again shortly.",
            request=request,
        )

    # ------------------------------------------------------------------
    # Catch-all for remaining domain exceptions — 500
    # ------------------------------------------------------------------
    @app.exception_handler(PrabhuBaseException)
    async def handle_domain_exception(
        request: Request, exc: PrabhuBaseException
    ) -> JSONResponse:
        logger.error(
            "unhandled_domain_exception",
            path=request.url.path,
            exc_type=type(exc).__name__,
            error=str(exc),
        )
        return _json_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            _safe_detail(exc),
            request=request,
        )

    # ------------------------------------------------------------------
    # Catch-all for unexpected Python exceptions — 500
    # This should never fire in normal operation.
    # If it does, a domain exception is missing for a real error case.
    # ------------------------------------------------------------------
    @app.exception_handler(Exception)
    async def handle_unhandled_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            exc_type=type(exc).__name__,
        )
        return _json_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An unexpected error occurred. Please try again.",
            request=request,
        )
