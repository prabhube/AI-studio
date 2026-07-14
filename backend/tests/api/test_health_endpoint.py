"""
API tests for the /health endpoint.

These tests verify the response shape and status code without requiring
a live database or Redis, by patching the infrastructure check functions.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Tests for GET /api/v1/health."""

    async def test_health_returns_200_when_all_services_ok(self, client):
        """When both DB and Redis are healthy, expect HTTP 200 and status='ok'."""
        with (
            patch(
                "app.api.v1.endpoints.health.check_database_connection",
                return_value=3.5,
            ),
            patch(
                "app.api.v1.endpoints.health.check_redis_connection",
                return_value=1.2,
            ),
        ):
            response = await client.get("/api/v1/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["services"]["postgres"]["status"] == "ok"
        assert body["services"]["redis"]["status"] == "ok"
        assert body["services"]["postgres"]["latency_ms"] == 3.5
        assert "version" in body
        assert "uptime_seconds" in body

    async def test_health_returns_503_when_database_is_down(self, client):
        """When the DB is unreachable, expect HTTP 503."""
        from app.core.exceptions import DatabaseError

        with (
            patch(
                "app.api.v1.endpoints.health.check_database_connection",
                side_effect=DatabaseError("Connection refused"),
            ),
            patch(
                "app.api.v1.endpoints.health.check_redis_connection",
                return_value=1.2,
            ),
        ):
            response = await client.get("/api/v1/health")

        assert response.status_code == 503
        body = response.json()
        assert body["services"]["postgres"]["status"] == "error"

    async def test_health_returns_200_when_only_redis_is_down(self, client):
        """
        Redis is non-critical — app can still serve requests.
        Expect HTTP 200 with status='degraded'.
        """
        from app.core.exceptions import CacheError

        with (
            patch(
                "app.api.v1.endpoints.health.check_database_connection",
                return_value=4.0,
            ),
            patch(
                "app.api.v1.endpoints.health.check_redis_connection",
                side_effect=CacheError("Redis unavailable"),
            ),
        ):
            response = await client.get("/api/v1/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "degraded"
        assert body["services"]["redis"]["status"] == "error"
        assert body["services"]["postgres"]["status"] == "ok"

    async def test_health_includes_request_id_header(self, client):
        """Response must include X-Request-ID header."""
        with (
            patch(
                "app.api.v1.endpoints.health.check_database_connection",
                return_value=1.0,
            ),
            patch(
                "app.api.v1.endpoints.health.check_redis_connection",
                return_value=1.0,
            ),
        ):
            response = await client.get("/api/v1/health")

        assert "x-request-id" in response.headers

    async def test_health_includes_timing_header(self, client):
        """Response must include X-Process-Time-Ms header."""
        with (
            patch(
                "app.api.v1.endpoints.health.check_database_connection",
                return_value=1.0,
            ),
            patch(
                "app.api.v1.endpoints.health.check_redis_connection",
                return_value=1.0,
            ),
        ):
            response = await client.get("/api/v1/health")

        assert "x-process-time-ms" in response.headers
        assert float(response.headers["x-process-time-ms"]) >= 0
