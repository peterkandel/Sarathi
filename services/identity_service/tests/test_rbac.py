from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_citizen_me_and_admin_routes_respect_roles(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "citizen2@example.com",
            "username": "citizen02",
            "password": "verystrongpassword",
            "full_name": "Citizen Two",
        },
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "citizen2@example.com", "password": "verystrongpassword"},
    )
    token = login_response.json()["access_token"]

    citizen_response = await client.get(
        "/api/v1/me",
        headers={"authorization": f"Bearer {token}"},
    )
    assert citizen_response.status_code == 200

    admin_response = await client.get(
        "/api/v1/admin/users",
        headers={"authorization": f"Bearer {token}"},
    )
    assert admin_response.status_code in {403, 404}
