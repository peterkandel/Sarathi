from __future__ import annotations

import pytest
from httpx import AsyncClient


def admin_headers(subject: str = "admin-001") -> dict[str, str]:
    return {
        "x-sarathi-subject": subject,
        "x-sarathi-roles": "Administrator",
        "x-sarathi-agency-id": "agency-01",
    }


def citizen_headers(subject: str = "citizen-001") -> dict[str, str]:
    return {
        "x-sarathi-subject": subject,
        "x-sarathi-roles": "Citizen",
        "x-sarathi-agency-id": "agency-01",
    }


@pytest.mark.asyncio
async def test_access_control_and_definition_validation(client: AsyncClient):
    forbidden_response = await client.post(
        "/api/v1/definitions",
        headers=citizen_headers(),
        json={"code": "license", "name": "License Workflow", "version": "1.0"},
    )
    assert forbidden_response.status_code == 403

    create_response = await client.post(
        "/api/v1/definitions",
        headers=admin_headers(),
        json={"code": "license", "name": "License Workflow", "version": "1.0"},
    )
    assert create_response.status_code == 201
    definition_id = create_response.json()["id"]

    duplicate_response = await client.post(
        "/api/v1/definitions",
        headers=admin_headers(),
        json={"code": "license", "name": "License Workflow Duplicate", "version": "1.0"},
    )
    assert duplicate_response.status_code == 409

    invalid_transition_response = await client.post(
        f"/api/v1/definitions/{definition_id}/transitions",
        headers=admin_headers(),
        json={
            "from_state_id": "00000000-0000-0000-0000-000000000000",
            "to_state_id": "00000000-0000-0000-0000-000000000001",
            "action": "submit",
            "allowed_roles": ["Citizen"],
        },
    )
    assert invalid_transition_response.status_code in {400, 404}


@pytest.mark.asyncio
async def test_definition_submission_approval_and_escalation(client: AsyncClient):
    definition_response = await client.post(
        "/api/v1/definitions",
        headers=admin_headers(),
        json={"code": "citizen-support", "name": "Citizen Support", "version": "1.0"},
    )
    assert definition_response.status_code == 201
    definition_id = definition_response.json()["id"]

    states = {}
    for payload in [
        {"code": "draft", "name": "Draft", "state_kind": "DRAFT", "is_initial": True, "sort_order": 1},
        {"code": "pending", "name": "Pending Approval", "state_kind": "PENDING_APPROVAL", "sort_order": 2},
        {"code": "approved", "name": "Approved", "state_kind": "APPROVED", "is_terminal": True, "sort_order": 3},
        {"code": "rejected", "name": "Rejected", "state_kind": "REJECTED", "is_terminal": True, "sort_order": 4},
        {"code": "escalated", "name": "Escalated", "state_kind": "ESCALATED", "is_terminal": True, "sort_order": 5},
    ]:
        response = await client.post(f"/api/v1/definitions/{definition_id}/states", headers=admin_headers(), json=payload)
        assert response.status_code == 201
        states[payload["code"]] = response.json()

    for payload in [
        {"from_state_id": states["draft"]["id"], "to_state_id": states["pending"]["id"], "action": "review", "allowed_roles": ["Citizen"]},
        {"from_state_id": states["pending"]["id"], "to_state_id": states["approved"]["id"], "action": "approve", "allowed_roles": ["Clerk", "Reviewer"]},
        {"from_state_id": states["pending"]["id"], "to_state_id": states["rejected"]["id"], "action": "reject", "allowed_roles": ["Reviewer", "Manager"]},
        {"from_state_id": states["pending"]["id"], "to_state_id": states["escalated"]["id"], "action": "escalate", "allowed_roles": ["Administrator"]},
    ]:
        response = await client.post(f"/api/v1/definitions/{definition_id}/transitions", headers=admin_headers(), json=payload)
        assert response.status_code == 201

    chain_response = await client.post(
        f"/api/v1/definitions/{definition_id}/approval-chains",
        headers=admin_headers(),
        json={"source_state_id": states["pending"]["id"], "name": "Support review chain"},
    )
    assert chain_response.status_code == 201
    chain_id = chain_response.json()["id"]

    step_one = await client.post(
        f"/api/v1/approval-chains/{chain_id}/steps",
        headers=admin_headers(),
        json={"step_order": 1, "required_role": "Clerk", "step_name": "Clerk review"},
    )
    assert step_one.status_code == 201
    step_two = await client.post(
        f"/api/v1/approval-chains/{chain_id}/steps",
        headers=admin_headers(),
        json={"step_order": 2, "required_role": "Reviewer", "step_name": "Reviewer review"},
    )
    assert step_two.status_code == 201

    escalation_rule_response = await client.post(
        f"/api/v1/definitions/{definition_id}/escalation-rules",
        headers=admin_headers(),
        json={
            "source_state_id": states["pending"]["id"],
            "target_state_id": states["escalated"]["id"],
            "after_minutes": 0,
            "target_role": "Manager",
        },
    )
    assert escalation_rule_response.status_code == 201

    submit_response = await client.post(
        "/api/v1/applications/submit",
        headers=citizen_headers(),
        json={
            "definition_code": "citizen-support",
            "definition_version": "1.0",
            "entity_type": "citizen_profile",
            "entity_id": "profile-001",
            "title": "Support request",
            "payload": {"reason": "Need document correction"},
            "application_metadata": {"source": "portal"},
        },
    )
    assert submit_response.status_code == 201
    application_id = submit_response.json()["id"]
    assert submit_response.json()["current_state_id"] == states["draft"]["id"]

    review_response = await client.post(
        f"/api/v1/applications/{application_id}/transition?action=review",
        headers=citizen_headers(),
        json={"notes": "Submit for review", "payload": {"submitted": True}},
    )
    assert review_response.status_code == 200
    assert review_response.json()["current_state_id"] == states["pending"]["id"]

    clerk_approve = await client.post(
        f"/api/v1/applications/{application_id}/approve",
        headers={"x-sarathi-subject": "clerk-001", "x-sarathi-roles": "Clerk", "x-sarathi-agency-id": "agency-01"},
        json={"notes": "Clerk approved"},
    )
    assert clerk_approve.status_code == 200
    assert clerk_approve.json()["current_step_order"] == 2

    reviewer_approve = await client.post(
        f"/api/v1/applications/{application_id}/approve",
        headers={"x-sarathi-subject": "reviewer-001", "x-sarathi-roles": "Reviewer", "x-sarathi-agency-id": "agency-01"},
        json={"notes": "Reviewer approved"},
    )
    assert reviewer_approve.status_code == 200
    assert reviewer_approve.json()["current_state_id"] == states["approved"]["id"]
    assert reviewer_approve.json()["status"] == "COMPLETED"

    escalation_submit = await client.post(
        "/api/v1/applications/submit",
        headers=citizen_headers("citizen-002"),
        json={
            "definition_code": "citizen-support",
            "definition_version": "1.0",
            "entity_type": "citizen_profile",
            "entity_id": "profile-002",
            "title": "Escalation request",
            "payload": {},
        },
    )
    assert escalation_submit.status_code == 201
    escalation_application_id = escalation_submit.json()["id"]

    await client.post(
        f"/api/v1/applications/{escalation_application_id}/transition?action=review",
        headers=citizen_headers("citizen-002"),
        json={"notes": "Move to pending"},
    )
    escalation_result = await client.post(
        f"/api/v1/applications/{escalation_application_id}/escalate",
        headers=admin_headers(),
        json={"notes": "Escalated by admin"},
    )
    assert escalation_result.status_code == 200
    assert escalation_result.json()["current_state_id"] == states["escalated"]["id"]


@pytest.mark.asyncio
async def test_escalation_and_validation(client: AsyncClient):
    definition_response = await client.post(
        "/api/v1/definitions",
        headers=admin_headers(),
        json={"code": "validation-flow", "name": "Validation Flow", "version": "1.0"},
    )
    assert definition_response.status_code == 201
    definition_id = definition_response.json()["id"]

    invalid_escalation_response = await client.post(
        f"/api/v1/definitions/{definition_id}/escalation-rules",
        headers=admin_headers(),
        json={
            "source_state_id": "00000000-0000-0000-0000-000000000000",
            "target_state_id": "00000000-0000-0000-0000-000000000001",
            "after_minutes": -1,
            "target_role": "Manager",
        },
    )
    assert invalid_escalation_response.status_code in {400, 422, 404}

    state_response = await client.post(
        f"/api/v1/definitions/{definition_id}/states",
        headers=admin_headers(),
        json={"code": "only", "name": "Only", "is_initial": True, "is_terminal": True, "sort_order": 1},
    )
    assert state_response.status_code == 201

    bad_transition_response = await client.post(
        f"/api/v1/definitions/{definition_id}/transitions",
        headers=admin_headers(),
        json={
            "from_state_id": state_response.json()["id"],
            "to_state_id": state_response.json()["id"],
            "action": "loop",
            "allowed_roles": ["NotARole"],
        },
    )
    assert bad_transition_response.status_code == 201
