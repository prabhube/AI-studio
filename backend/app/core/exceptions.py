"""
Domain exception hierarchy for Prabhu AI Studio.

All domain errors inherit from PrabhuBaseException so callers
can catch the entire tree with a single except clause.
"""

from typing import Any


class PrabhuBaseException(Exception):
    """Root exception for all application-level errors."""

    def __init__(self, message: str, detail: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


# ----------------------------
# Authentication & Authorization
# ----------------------------


class AuthenticationError(PrabhuBaseException):
    """Raised when credentials are invalid or missing."""


class AuthorizationError(PrabhuBaseException):
    """Raised when a user lacks permission for an action."""


class TokenExpiredError(AuthenticationError):
    """Raised when a JWT token has expired."""


class TokenInvalidError(AuthenticationError):
    """Raised when a JWT token is malformed or has an invalid signature."""


# ----------------------------
# Resource Errors
# ----------------------------


class ResourceNotFoundError(PrabhuBaseException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, identifier: Any) -> None:
        super().__init__(
            message=f"{resource} with identifier '{identifier}' was not found.",
            detail={"resource": resource, "identifier": str(identifier)},
        )


class ResourceAlreadyExistsError(PrabhuBaseException):
    """Raised when attempting to create a duplicate resource."""

    def __init__(self, resource: str, identifier: Any) -> None:
        super().__init__(
            message=f"{resource} '{identifier}' already exists.",
            detail={"resource": resource, "identifier": str(identifier)},
        )


# ----------------------------
# Validation Errors
# ----------------------------


class ValidationError(PrabhuBaseException):
    """Raised when business-rule validation fails (not Pydantic schema errors)."""


class InvalidInputError(ValidationError):
    """Raised when user input fails domain-level validation."""


# ----------------------------
# AI Provider Errors
# ----------------------------


class AIProviderError(PrabhuBaseException):
    """Base class for all AI provider errors."""


class LLMProviderError(AIProviderError):
    """Raised when the language model provider fails."""


class ImageProviderError(AIProviderError):
    """Raised when the image generation provider fails."""


class TTSProviderError(AIProviderError):
    """Raised when the text-to-speech provider fails."""


class STTProviderError(AIProviderError):
    """Raised when the speech-to-text provider fails."""


class VideoProviderError(AIProviderError):
    """Raised when the video generation provider fails."""


class ProviderNotConfiguredError(AIProviderError):
    """Raised when a provider is requested but has not been configured."""

    def __init__(self, provider_name: str) -> None:
        super().__init__(
            message=f"AI provider '{provider_name}' is not configured. "
            "Check your .env settings.",
            detail={"provider": provider_name},
        )


# ----------------------------
# Infrastructure Errors
# ----------------------------


class DatabaseError(PrabhuBaseException):
    """Raised when a database operation fails unexpectedly."""


class CacheError(PrabhuBaseException):
    """Raised when a Redis cache operation fails."""


class StorageError(PrabhuBaseException):
    """Raised when a file storage operation fails."""


class ExternalServiceError(PrabhuBaseException):
    """Raised when an external HTTP service call fails."""
