"""Tests for authentication routes."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

SIGNUP_PAYLOAD = {
    "full_name": "Test Admin",
    "username": "tadmin",
    "email": "tadmin@test.com",
    "password": "password",
}


async def _signup_and_login(client: AsyncClient) -> dict:
    await client.post("/auth/signup", json=SIGNUP_PAYLOAD)
    resp = await client.post(
        "/auth/login",
        json={"email": SIGNUP_PAYLOAD["email"], "password": SIGNUP_PAYLOAD["password"]},
    )
    return resp.json()


class TestSignup:
    async def test_signup_creates_user(self, client: AsyncClient):
        response = await client.post("/auth/signup", json=SIGNUP_PAYLOAD)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == SIGNUP_PAYLOAD["email"]
        assert data["username"] == SIGNUP_PAYLOAD["username"]

    async def test_duplicate_username_rejected(self, client: AsyncClient):
        await client.post("/auth/signup", json=SIGNUP_PAYLOAD)
        response = await client.post("/auth/signup", json=SIGNUP_PAYLOAD)
        assert response.status_code == 403


class TestLogin:
    async def test_successful_login_returns_tokens(self, client: AsyncClient):
        await client.post("/auth/signup", json=SIGNUP_PAYLOAD)
        response = await client.post(
            "/auth/login",
            json={"email": SIGNUP_PAYLOAD["email"], "password": SIGNUP_PAYLOAD["password"]},
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["username"] == SIGNUP_PAYLOAD["username"]

    async def test_invalid_password_returns_401(self, client: AsyncClient):
        await client.post("/auth/signup", json=SIGNUP_PAYLOAD)
        response = await client.post(
            "/auth/login",
            json={"email": SIGNUP_PAYLOAD["email"], "password": "wrong"},
        )
        assert response.status_code == 401

    async def test_unknown_email_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/auth/login",
            json={"email": "nobody@test.com", "password": "password"},
        )
        assert response.status_code == 401


class TestRefreshToken:
    async def test_refresh_returns_new_access_token(self, client: AsyncClient):
        tokens = await _signup_and_login(client)
        refresh_token = tokens["refresh_token"]

        response = await client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


class TestLogout:
    async def test_logout_succeeds(self, client: AsyncClient):
        tokens = await _signup_and_login(client)
        response = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully!"


class TestGetUser:
    async def test_get_user_returns_profile(self, client: AsyncClient):
        tokens = await _signup_and_login(client)
        response = await client.get(
            "/auth/user",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == SIGNUP_PAYLOAD["email"]

    async def test_unauthenticated_request_returns_403_or_401(self, client: AsyncClient):
        response = await client.get("/auth/user")
        assert response.status_code in (401, 403)
