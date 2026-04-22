"""Tests for URL shortening routes."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

SIGNUP_PAYLOAD = {
    "full_name": "URL Tester",
    "username": "urltester",
    "email": "urltester@test.com",
    "password": "password",
}


async def _get_auth_headers(client: AsyncClient) -> dict:
    await client.post("/auth/signup", json=SIGNUP_PAYLOAD)
    resp = await client.post(
        "/auth/login",
        json={"email": SIGNUP_PAYLOAD["email"], "password": SIGNUP_PAYLOAD["password"]},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestShorten:
    async def test_shorten_valid_url(self, client: AsyncClient):
        headers = await _get_auth_headers(client)
        response = await client.post(
            "/shorten",
            json={"original_url": "https://example.com/long-url"},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "shortened_url" in data
        assert "short_code" in data

    async def test_shorten_invalid_url_returns_400(self, client: AsyncClient):
        headers = await _get_auth_headers(client)
        response = await client.post(
            "/shorten",
            json={"original_url": "not-a-url"},
            headers=headers,
        )
        assert response.status_code == 400

    async def test_shorten_with_custom_shortcode(self, client: AsyncClient):
        headers = await _get_auth_headers(client)
        response = await client.post(
            "/shorten",
            json={"original_url": "https://example.com/custom", "short_code": "mycustom"},
            headers=headers,
        )
        assert response.status_code == 201
        assert response.json()["short_code"] == "mycustom"

    async def test_duplicate_custom_shortcode_returns_409(self, client: AsyncClient):
        headers = await _get_auth_headers(client)
        await client.post(
            "/shorten",
            json={"original_url": "https://example.com/1", "short_code": "dupcode"},
            headers=headers,
        )
        response = await client.post(
            "/shorten",
            json={"original_url": "https://example.com/2", "short_code": "dupcode"},
            headers=headers,
        )
        assert response.status_code == 409

    async def test_unauthenticated_shorten_returns_403(self, client: AsyncClient):
        response = await client.post(
            "/shorten",
            json={"original_url": "https://example.com"},
        )
        assert response.status_code in (401, 403)


class TestRedirect:
    async def test_redirect_follows_to_original_url(self, client: AsyncClient):
        headers = await _get_auth_headers(client)
        shorten_resp = await client.post(
            "/shorten",
            json={"original_url": "https://example.com"},
            headers=headers,
        )
        short_code = shorten_resp.json()["short_code"]

        redirect_resp = await client.get(f"/{short_code}", follow_redirects=False)
        assert redirect_resp.status_code == 302
        assert redirect_resp.headers["location"] == "https://example.com"

    async def test_unknown_shortcode_returns_404(self, client: AsyncClient):
        response = await client.get("/unknownxyz", follow_redirects=False)
        assert response.status_code == 404


class TestGetShortenedUrl:
    async def test_get_shortened_url_by_shortcode(self, client: AsyncClient):
        headers = await _get_auth_headers(client)
        shorten_resp = await client.post(
            "/shorten",
            json={"original_url": "https://example.com"},
            headers=headers,
        )
        short_code = shorten_resp.json()["short_code"]

        response = await client.get(f"/shortened/{short_code}", headers=headers)
        assert response.status_code == 200
        assert short_code in response.json()


class TestDeleteUrl:
    async def test_delete_url(self, client: AsyncClient):
        headers = await _get_auth_headers(client)
        shorten_resp = await client.post(
            "/shorten",
            json={"original_url": "https://example.com/delete-me"},
            headers=headers,
        )
        short_code = shorten_resp.json()["short_code"]

        delete_resp = await client.delete(f"/shortened/{short_code}", headers=headers)
        assert delete_resp.status_code == 200
        assert delete_resp.json()["message"] == "Url successfully deleted"

        # Verify redirect now returns 404
        verify_resp = await client.get(f"/{short_code}", follow_redirects=False)
        assert verify_resp.status_code == 404

    async def test_delete_nonexistent_url_returns_404(self, client: AsyncClient):
        headers = await _get_auth_headers(client)
        response = await client.delete("/shortened/doesnotexist", headers=headers)
        assert response.status_code == 404


class TestHistory:
    async def test_history_returns_created_urls(self, client: AsyncClient):
        headers = await _get_auth_headers(client)
        urls = [
            "https://example.com/hist1",
            "https://example.com/hist2",
            "https://example.com/hist3",
        ]
        for u in urls:
            await client.post("/shorten", json={"original_url": u}, headers=headers)

        response = await client.get("/history", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= len(urls)


class TestAnalytics:
    async def test_analytics_returns_data(self, client: AsyncClient):
        headers = await _get_auth_headers(client)
        shorten_resp = await client.post(
            "/shorten",
            json={"original_url": "https://example.com/analytics"},
            headers=headers,
        )
        short_code = shorten_resp.json()["short_code"]

        response = await client.get(f"/analytics/{short_code}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["short_code"] == short_code
        assert "total_clicks" in data
        assert "clicks_by_source" in data


class TestQRCode:
    async def test_qr_code_returns_png(self, client: AsyncClient):
        headers = await _get_auth_headers(client)
        shorten_resp = await client.post(
            "/shorten",
            json={"original_url": "https://example.com/qr"},
            headers=headers,
        )
        short_code = shorten_resp.json()["short_code"]

        response = await client.get(f"/{short_code}/qrcode", headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
