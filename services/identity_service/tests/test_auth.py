from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_login_refresh_logout_and_password_reset(client: AsyncClient):
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "citizen@example.com",
            "username": "citizen01",
            "password": "verystrongpassword",
            "full_name": "Citizen One",
        },
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "citizen@example.com"

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "citizen@example.com", "password": "verystrongpassword", "device_id": "device-1"},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body["access_token"]
    assert login_body["refresh_token"]
    assert login_body["session_id"]

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"session_id": login_body["session_id"], "refresh_token": login_body["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    refreshed_body = refresh_response.json()
    assert refreshed_body["access_token"]
    assert refreshed_body["refresh_token"]

    logout_response = await client.post(
        "/api/v1/auth/logout",
        json={"session_id": refreshed_body["session_id"]},
    )
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Logged out"

    reset_request = await client.post("/api/v1/auth/password-reset/request", json={"email": "citizen@example.com"})
    assert reset_request.status_code == 200

    reset_confirm = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "invalid-token", "new_password": "an-even-stronger-password"},
    )
    assert reset_confirm.status_code == 400
