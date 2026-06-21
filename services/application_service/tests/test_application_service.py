from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

import pytest
from httpx import AsyncClient


class StubWorkflowClient:
    def __init__(self) -> None:
        self.submissions: list[dict[str, object]] = []
        self.applications: dict[str, dict[str, object]] = {}

    async def submit_application(self, **kwargs):
        workflow_application_id = "11111111-1111-1111-1111-111111111111"
        payload = {
            "id": workflow_application_id,
            "status": "SUBMITTED",
            "current_state_id": "22222222-2222-2222-2222-222222222222",
            "workflow_current_state_code": "pending_review",
        }
        self.submissions.append(kwargs)
        self.applications[workflow_application_id] = payload
        return payload

    async def get_application(self, workflow_application_id: str):
        return self.applications[workflow_application_id]


@pytest.fixture()
async def workflow_stub(client: AsyncClient):
    from app.api.dependencies import get_workflow_client
    from app.main import app

    stub = StubWorkflowClient()
    app.dependency_overrides[get_workflow_client] = lambda: stub
    yield stub
    app.dependency_overrides.pop(get_workflow_client, None)


def citizen_headers(subject: str = "citizen-001") -> dict[str, str]:
    return {
        "x-sarathi-subject": subject,
        "x-sarathi-roles": "Citizen",
        "x-sarathi-agency-id": "agency-01",
    }


def admin_headers(subject: str = "admin-001") -> dict[str, str]:
    return {
        "x-sarathi-subject": subject,
        "x-sarathi-roles": "Administrator",
        "x-sarathi-agency-id": "agency-01",
    }


@pytest.mark.asyncio
async def test_create_attach_submit_status_history(client: AsyncClient, workflow_stub: StubWorkflowClient):
    create_response = await client.post(
        "/api/v1/applications",
        headers=citizen_headers(),
        json={
            "workflow_definition_code": "citizen-support",
            "workflow_definition_version": "1.0",
            "entity_type": "citizen_profile",
            "entity_id": "profile-001",
            "title": "Name correction",
            "description": "Fix spelling",
            "payload": {"reason": "spelling"},
            "application_metadata": {"source": "portal"},
        },
    )
    assert create_response.status_code == 201
    application_id = create_response.json()["id"]
    assert create_response.json()["application_status"] == "DRAFT"

    attach_response = await client.post(
        f"/api/v1/applications/{application_id}/documents",
        headers=citizen_headers(),
        json={
            "document_type": "PROOF_OF_ADDRESS",
            "file_name": "proof.pdf",
            "mime_type": "application/pdf",
            "storage_key": "documents/proof.pdf",
            "checksum_sha256": "a" * 64,
            "size_bytes": 1024,
            "document_metadata": {"verified": False},
        },
    )
    assert attach_response.status_code == 201

    submit_response = await client.post(f"/api/v1/applications/{application_id}/submit", headers=citizen_headers())
    assert submit_response.status_code == 200
    assert submit_response.json()["application_status"] == "SUBMITTED"
    assert submit_response.json()["workflow_application_id"] == "11111111-1111-1111-1111-111111111111"

    status_response = await client.get(f"/api/v1/applications/{application_id}/status", headers=citizen_headers())
    assert status_response.status_code == 200
    assert status_response.json()["application_status"] == "SUBMITTED"
    assert status_response.json()["document_count"] == 1

    history_response = await client.get(f"/api/v1/applications/{application_id}/history", headers=citizen_headers())
    assert history_response.status_code == 200
    assert len(history_response.json()) >= 3


@pytest.mark.asyncio
async def test_submission_requires_document(client: AsyncClient):
    create_response = await client.post(
        "/api/v1/applications",
        headers=citizen_headers("citizen-002"),
        json={
            "workflow_definition_code": "citizen-support",
            "workflow_definition_version": "1.0",
            "entity_type": "citizen_profile",
            "entity_id": "profile-002",
            "title": "Tax update",
        },
    )
    assert create_response.status_code == 201
    application_id = create_response.json()["id"]

    submit_response = await client.post(f"/api/v1/applications/{application_id}/submit", headers=citizen_headers("citizen-002"))
    assert submit_response.status_code == 400


@pytest.mark.asyncio
async def test_access_control_for_application(client: AsyncClient):
    create_response = await client.post(
        "/api/v1/applications",
        headers=citizen_headers("citizen-003"),
        json={
            "workflow_definition_code": "citizen-support",
            "workflow_definition_version": "1.0",
            "entity_type": "citizen_profile",
            "entity_id": "profile-003",
            "title": "Address change",
        },
    )
    application_id = create_response.json()["id"]

    forbidden_response = await client.get(f"/api/v1/applications/{application_id}", headers=citizen_headers("other-citizen"))
    assert forbidden_response.status_code == 403

    admin_response = await client.get(f"/api/v1/applications/{application_id}", headers=admin_headers())
    assert admin_response.status_code == 200
