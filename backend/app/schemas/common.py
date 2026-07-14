"""
Shared response envelope schemas used across all API endpoints.

Every API response — success or error — is wrapped in one of these
envelopes. Consistent response shapes simplify frontend error handling.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard single-object success response wrapper."""

    success: bool = True
    data: T
    message: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list response wrapper."""

    success: bool = True
    data: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorDetail(BaseModel):
    """Single validation error detail."""

    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    """Standard error response returned by all exception handlers."""

    success: bool = False
    error: str
    details: list[ErrorDetail] | None = None
    request_id: str | None = None


class ServiceStatus(BaseModel):
    """Status and timing for a single infrastructure dependency."""

    status: str                     # "ok" | "error" | "degraded"
    latency_ms: float | None = None
    detail: str | None = None


class HealthCheckResponse(BaseModel):
    """Response schema for the /health endpoint."""

    status: str                     # "ok" | "degraded" | "unhealthy"
    version: str
    environment: str
    uptime_seconds: float
    services: dict[str, ServiceStatus]
    disk: dict[str, Any] | None = None
