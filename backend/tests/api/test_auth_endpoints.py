"""
API integration tests for authentication endpoints.

Tests run against the full FastAPI stack with an in-memory SQLite DB.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRegisterEndpoint:
    async def test_register_success(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "brand@new.com",
                "username": "brandnew",
                "password": "BrandNew1",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["email"] == "brand@new.com"
        assert "hashed_password" not in body["data"]

    async def test_register_duplicate_email_returns_409(
        self, client: AsyncClient, test_user
    ):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "username": "anotheruser",
                "password": "AnotherPass1",
            },
        )
        assert response.status_code == 409

    async def test_register_weak_password_returns_422(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "username": "weakuser",
                "password": "short",
            },
        )
        assert response.status_code == 422

    async def test_register_invalid_email_returns_422(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "baduser",
                "password": "BadPass1",
            },
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestLoginEndpoint:
    async def test_login_success_returns_tokens(
        self, client: AsyncClient, test_user
    ):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass1"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body["data"]
        assert "refresh_token" in body["data"]
        assert body["data"]["token_type"] == "bearer"

    async def test_login_wrong_password_returns_401(
        self, client: AsyncClient, test_user
    ):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "WrongPassword1"},
        )
        assert response.status_code == 401

    async def test_login_unknown_email_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "SomePass1"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestRefreshEndpoint:
    async def test_refresh_returns_new_access_token(
        self, client: AsyncClient, test_user
    ):
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "TestPass1"},
        )
        refresh_token = login_response.json()["data"]["refresh_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()["data"]

    async def test_refresh_with_invalid_token_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUsersEndpoint:
    async def test_get_me_returns_current_user(
        self, client: AsyncClient, test_user, auth_headers
    ):
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["email"] == test_user.email

    async def test_get_me_without_token_returns_401(self, client: AsyncClient):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_list_users_requires_superuser(
        self, client: AsyncClient, auth_headers
    ):
        response = await client.get("/api/v1/users/", headers=auth_headers)
        assert response.status_code == 403

    async def test_list_users_accessible_by_superuser(
        self, client: AsyncClient, superuser_auth_headers
    ):
        response = await client.get(
            "/api/v1/users/", headers=superuser_auth_headers
        )
        assert response.status_code == 200
        assert "data" in response.json()
