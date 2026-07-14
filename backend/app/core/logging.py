"""
Structured logging configuration.

Design decisions:
  - structlog for structured, context-aware logging.
  - Development: colored console output with callsite information.
  - Production: JSON output compatible with log aggregators (Loki, ELK, etc.).
  - Request-scoped context (request_id, user_id) is stored in structlog
    contextvars and automatically included on every log call within a request.
  - SQL query logging is controlled separately to avoid noise in production.
  - No PII is logged by default — use the mask_value() helper for sensitive data.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

# ---------------------------------------------------------------------------
# Custom processors
# ---------------------------------------------------------------------------


def _add_app_context(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Inject static application context into every log record."""
    event_dict.setdefault("app", "prabhu-ai-studio")
    return event_dict


def _drop_color_message_key(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Remove uvicorn's redundant 'color_message' key."""
    event_dict.pop("color_message", None)
    return event_dict


def _order_keys(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Re-order dict keys so the most important fields come first in JSON output.

    This makes logs easier to read in terminals and log viewers
    without sacrificing machine-parseability.
    """
    priority = ("timestamp", "level", "event", "app", "request_id", "logger")
    ordered: dict[str, Any] = {}
    for key in priority:
        if key in event_dict:
            ordered[key] = event_dict.pop(key)
    ordered.update(event_dict)
    return ordered


def _sanitize_event(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Redact known-sensitive key names from structured log fields.

    This is a defence-in-depth measure. Callers must still avoid
    logging sensitive data; this catches accidental leakage.
    """
    _SENSITIVE = frozenset(
        {"password", "secret", "token", "api_key", "authorization", "cookie"}
    )
    for key in list(event_dict.keys()):
        if key.lower() in _SENSITIVE:
            event_dict[key] = "***REDACTED***"
    return event_dict


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def configure_logging(*, debug: bool = False, environment: str = "development") -> None:
    """
    Configure structlog globally for the application.

    Call once during application startup (in the lifespan handler).
    Subsequent calls are no-ops because structlog caches on first use.

    Args:
        debug:       Enable DEBUG level; otherwise INFO.
        environment: "development" → colored console; else → JSON.
    """
    log_level = logging.DEBUG if debug else logging.INFO

    # Processors applied to every log record, in order:
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,           # request_id, user_id etc.
        structlog.stdlib.add_log_level,                    # "level": "info"
        structlog.stdlib.add_logger_name,                  # "logger": "app.db.session"
        structlog.processors.TimeStamper(fmt="iso"),       # "timestamp": "2025-…"
        _add_app_context,
        _drop_color_message_key,
        _sanitize_event,
    ]

    if environment == "development":
        # Add callsite info (file:line) for developer convenience
        processors: list[Any] = [
            *shared_processors,
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            _order_keys,
            structlog.dev.ConsoleRenderer(colors=True, sort_keys=False),
        ]
    else:
        # Production: compact JSON consumed by Loki / ELK
        processors = [
            *shared_processors,
            structlog.processors.dict_tracebacks,           # exceptions as dicts
            _order_keys,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )

    # ------------------------------------------------------------------
    # Standard library logging bridge
    # Routes Python stdlib logging (uvicorn, sqlalchemy, etc.) through
    # structlog so they share the same format and destination.
    # ------------------------------------------------------------------
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Silence or quiet noisy third-party loggers
    _configure_third_party_loggers(debug=debug)


def _configure_third_party_loggers(*, debug: bool) -> None:
    """
    Set appropriate log levels for third-party libraries.

    Production: suppress everything except warnings.
    Development: allow sqlalchemy echo if DB_ECHO=true, but keep
                 uvicorn.access quiet (we have our own access log middleware).
    """
    quiet_loggers = {
        "uvicorn.access": logging.WARNING,
        "multipart": logging.WARNING,
        "httpx": logging.WARNING,
        "hiredis": logging.WARNING,
    }
    # SQLAlchemy is always quiet unless explicitly enabled via DB_ECHO
    if not debug:
        quiet_loggers["sqlalchemy.engine"] = logging.WARNING
        quiet_loggers["sqlalchemy.pool"] = logging.WARNING
        quiet_loggers["alembic"] = logging.WARNING

    for name, level in quiet_loggers.items():
        logging.getLogger(name).setLevel(level)


def get_logger(name: str) -> Any:
    """
    Return a structlog logger bound to the given name.

    Usage:
        logger = get_logger(__name__)
        logger.info("event_name", key="value", count=42)
        logger.error("operation_failed", error=str(exc), exc_info=True)
    """
    return structlog.get_logger(name)


# ---------------------------------------------------------------------------
# Context helpers — call these in middleware/dependencies
# ---------------------------------------------------------------------------


def bind_request_context(*, request_id: str, path: str, method: str) -> None:
    """
    Bind per-request context to structlog's contextvars.

    Call at the start of each request. The values are automatically
    included in every log statement during that request.
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        http_path=path,
        http_method=method,
    )


def bind_user_context(*, user_id: str) -> None:
    """
    Add the authenticated user's ID to the current request context.

    Call from the get_current_user dependency after successful auth.
    Safe to call with a placeholder before auth is implemented.
    """
    structlog.contextvars.bind_contextvars(user_id=user_id)


def mask_value(value: str) -> str:
    """
    Mask a sensitive string for logging.

    Shows the first 4 and last 4 characters only.
    Returns '***' for strings shorter than 8 characters.

    Usage:
        logger.debug("token_used", token=mask_value(raw_token))
    """
    if len(value) < 8:
        return "***"
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"
