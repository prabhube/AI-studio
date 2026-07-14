"""
Project API Endpoint Tests — Placeholders.

Tests to implement:
    - POST /projects/ creates project and returns 201
    - POST /projects/ without auth returns 401
    - GET  /projects/ returns paginated list for user
    - GET  /projects/{id} returns project owned by user
    - GET  /projects/{id} returns 404 for missing project
    - GET  /projects/{id} returns 403 for another user's project
    - PATCH /projects/{id} updates name and description
    - DELETE /projects/{id} returns 204

Implementation: Phase 2.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestProjectCreate:
    async def test_create_returns_201(self, client: AsyncClient, auth_headers):
        pytest.skip("Implementation: Phase 2")

    async def test_create_without_auth_returns_401(self, client: AsyncClient):
        pytest.skip("Implementation: Phase 2")


@pytest.mark.asyncio
class TestProjectList:
    async def test_list_returns_only_user_projects(self, client: AsyncClient, auth_headers):
        pytest.skip("Implementation: Phase 2")
