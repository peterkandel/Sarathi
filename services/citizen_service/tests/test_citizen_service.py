from __future__ import annotations

from datetime import date, datetime, timezone, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.domain.models import AuditEvent, CitizenProfile, CitizenshipRecord, DocumentMetadata


def auth_headers(subject: str, roles: str = "Citizen") -> dict[str, str]:
    return {
        "x-sarathi-subject": subject,
        "x-sarathi-roles": roles,
        "x-sarathi-agency-id": "municipality-01",
    }


@pytest.mark.asyncio
async def test_profile_record_and_document_crud(client: AsyncClient, db_session):
    headers = auth_headers("citizen-001")

    profile_response = await client.post(
        "/api/v1/profiles",
        headers=headers,
        json={
            "full_name": "Citizen One",
            "date_of_birth": "1990-01-01",
            "gender": "FEMALE",
                "email": "Citizen1@example.com",
            "phone_number": "+9779800000000",
            "primary_language": "Nepali",
            "current_address": "Kathmandu",
            "permanent_address": "Bhaktapur",
            "profile_metadata": {"source": "identity-service"},
        },
    )
    assert profile_response.status_code == 201
    profile = profile_response.json()
    profile_id = profile["id"]
    assert profile["identity_subject"] == "citizen-001"
    assert profile["email"] == "citizen1@example.com"

    my_profile_response = await client.get("/api/v1/profiles/me", headers=headers)
    assert my_profile_response.status_code == 200
    assert my_profile_response.json()["id"] == profile_id

    update_response = await client.patch(
        f"/api/v1/profiles/{profile_id}",
        headers=headers,
        json={"phone_number": "+9779800000001", "profile_status": "INACTIVE"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["phone_number"] == "+9779800000001"
    assert update_response.json()["profile_status"] == "INACTIVE"

    record_response = await client.post(
        f"/api/v1/profiles/{profile_id}/citizenship-records",
        headers=headers,
        json={
            "certificate_number": "CIT-123456",
            "issued_on": "2015-06-01",
            "issuing_office": "District Administration Office, Kathmandu",
            "status": "ACTIVE",
            "record_metadata": {"verified": True},
        },
    )
    assert record_response.status_code == 201
    record = record_response.json()
    record_id = record["id"]
    assert record["certificate_number"] == "CIT-123456"

    records_response = await client.get(f"/api/v1/profiles/{profile_id}/citizenship-records", headers=headers)
    assert records_response.status_code == 200
    assert len(records_response.json()) == 1

    record_update_response = await client.patch(
        f"/api/v1/citizenship-records/{record_id}",
        headers=headers,
        json={"status": "SUSPENDED", "notes": "Verification review pending"},
    )
    assert record_update_response.status_code == 200
    assert record_update_response.json()["status"] == "SUSPENDED"

    document_response = await client.post(
        f"/api/v1/profiles/{profile_id}/documents",
        headers=headers,
        json={
            "document_type": "CITIZENSHIP_CERTIFICATE",
            "file_name": "citizenship.pdf",
            "mime_type": "application/pdf",
            "storage_key": "citizens/001/citizenship.pdf",
            "checksum_sha256": "a" * 64,
            "size_bytes": 2048,
            "document_status": "UPLOADED",
            "document_metadata": {"page_count": 2},
        },
    )
    assert document_response.status_code == 201
    document = document_response.json()
    document_id = document["id"]

    document_update_response = await client.patch(
        f"/api/v1/documents/{document_id}",
        headers=headers,
        json={"document_status": "VERIFIED", "verified_by_subject": "citizen-001"},
    )
    assert document_update_response.status_code == 200
    assert document_update_response.json()["document_status"] == "VERIFIED"

    delete_response = await client.delete(f"/api/v1/documents/{document_id}", headers=headers)
    assert delete_response.status_code == 200

    audit_rows = (await db_session.execute(AuditEvent.__table__.select())).all()
    assert len(audit_rows) >= 5


@pytest.mark.asyncio
async def test_access_scopes_to_owner_or_admin(client: AsyncClient):
    citizen_headers = auth_headers("citizen-002")
    other_headers = auth_headers("citizen-003")
    admin_headers = auth_headers("admin-001", roles="Administrator")

    create_response = await client.post(
        "/api/v1/profiles",
        headers=citizen_headers,
        json={
            "full_name": "Citizen Two",
            "date_of_birth": "1992-02-02",
        },
    )
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]

    forbidden_response = await client.get(f"/api/v1/profiles/{profile_id}", headers=other_headers)
    assert forbidden_response.status_code == 403

    admin_response = await client.get(f"/api/v1/profiles/{profile_id}", headers=admin_headers)
    assert admin_response.status_code == 200


@pytest.mark.asyncio
async def test_validation_rejects_invalid_payloads(client: AsyncClient):
    headers = auth_headers("citizen-004")

    future_birth_response = await client.post(
        "/api/v1/profiles",
        headers=headers,
        json={
            "full_name": "Future Citizen",
            "date_of_birth": (date.today() + timedelta(days=1)).isoformat(),
        },
    )
    assert future_birth_response.status_code == 422

    create_response = await client.post(
        "/api/v1/profiles",
        headers=headers,
        json={
            "full_name": "Citizen Four",
            "date_of_birth": "1991-03-03",
        },
    )
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]

    bad_checksum_response = await client.post(
        f"/api/v1/profiles/{profile_id}/documents",
        headers=headers,
        json={
            "document_type": "OTHER",
            "file_name": "file.txt",
            "mime_type": "text/plain",
            "storage_key": "citizens/004/file.txt",
            "checksum_sha256": "not-a-sha256",
            "size_bytes": 1,
        },
    )
    assert bad_checksum_response.status_code == 422