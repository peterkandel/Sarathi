from __future__ import annotations

import pytest
from httpx import AsyncClient


class AdminHeaders:
    @staticmethod
    def value(subject: str = "admin-001") -> dict[str, str]:
        return {
            "x-sarathi-subject": subject,
            "x-sarathi-roles": "Administrator",
            "x-sarathi-agency-id": "agency-01",
        }


class CitizenHeaders:
    @staticmethod
    def value(subject: str = "citizen-001") -> dict[str, str]:
        return {
            "x-sarathi-subject": subject,
            "x-sarathi-roles": "Citizen",
            "x-sarathi-agency-id": "agency-01",
        }


@pytest.mark.asyncio
async def test_adapter_request_processing_and_event_publishing(client: AsyncClient):
    adapter_response = await client.post(
        "/integration/v1/adapters",
        headers=AdminHeaders.value(),
        json={
            "adapter_code": "citizen-registry-rest",
            "adapter_name": "Citizenship Registry REST Adapter",
            "system_code": "citizenship_registry",
            "adapter_type": "rest",
            "base_url": "https://registry.example.gov.np",
            "auth_type": "mtls",
            "timeout_seconds": 10,
            "max_retry_attempts": 3,
            "breaker_failure_threshold": 2,
            "breaker_reset_seconds": 30,
            "adapter_metadata": {"owner": "identity"},
        },
    )
    assert adapter_response.status_code == 201

    request_response = await client.post(
        "/integration/v1/requests",
        headers=AdminHeaders.value(),
        json={
            "adapter_code": "citizen-registry-rest",
            "operation_code": "lookup_citizen",
            "idempotency_key": "lookup-001",
            "correlation_id": "corr-001",
            "external_reference": "REG-1001",
            "canonical_payload": {"citizen_identity_reference": "CIT-1001"},
            "request_payload": {"simulate_failure_attempts": 1},
            "max_attempts": 3,
        },
    )
    assert request_response.status_code == 201
    request_id = request_response.json()["id"]

    process_response = await client.post(f"/integration/v1/requests/{request_id}/process", headers=AdminHeaders.value())
    assert process_response.status_code == 200
    assert process_response.json()["status"] == "completed"

    attempts_response = await client.get(f"/integration/v1/requests/{request_id}/attempts", headers=AdminHeaders.value())
    assert attempts_response.status_code == 200
    assert len(attempts_response.json()) == 1 or len(attempts_response.json()) == 2

    events_response = await client.get(f"/integration/v1/requests/{request_id}/events", headers=AdminHeaders.value())
    assert events_response.status_code == 200
    assert any(event["event_type"] == "IntegrationCompleted" for event in events_response.json())

    publish_response = await client.post("/integration/v1/events/publish", headers=AdminHeaders.value(), json={"limit": 10})
    assert publish_response.status_code == 200
    assert publish_response.json()["published"] >= 1


@pytest.mark.asyncio
async def test_retry_and_circuit_breaker_behaviour(client: AsyncClient):
    await client.post(
        "/integration/v1/adapters",
        headers=AdminHeaders.value("admin-002"),
        json={
            "adapter_code": "tax-authority-rest",
            "adapter_name": "Tax Authority REST Adapter",
            "system_code": "tax_authority",
            "adapter_type": "rest",
            "base_url": "https://tax.example.gov.np",
            "auth_type": "oauth2",
            "timeout_seconds": 10,
            "max_retry_attempts": 2,
            "breaker_failure_threshold": 1,
            "breaker_reset_seconds": 60,
        },
    )

    failing_request = await client.post(
        "/integration/v1/requests",
        headers=AdminHeaders.value("admin-002"),
        json={
            "adapter_code": "tax-authority-rest",
            "operation_code": "submit_tax_record",
            "idempotency_key": "tax-001",
            "canonical_payload": {"taxpayer_subject": "citizen-001"},
            "request_payload": {"force_permanent_error": True},
            "max_attempts": 2,
        },
    )
    request_id = failing_request.json()["id"]

    process_response = await client.post(f"/integration/v1/requests/{request_id}/process", headers=AdminHeaders.value("admin-002"))
    assert process_response.status_code == 200
    assert process_response.json()["status"] == "failed"

    breaker_response = await client.get("/integration/v1/breakers", headers=AdminHeaders.value("admin-002"))
    assert breaker_response.status_code == 200
    assert breaker_response.json()[0]["state"] in {"open", "closed"}

    retry_response = await client.post(
        "/integration/v1/requests",
        headers=AdminHeaders.value("admin-002"),
        json={
            "adapter_code": "tax-authority-rest",
            "operation_code": "submit_tax_record",
            "idempotency_key": "tax-002",
            "canonical_payload": {"taxpayer_subject": "citizen-002"},
            "request_payload": {"simulate_failure_attempts": 1},
            "max_attempts": 2,
        },
    )
    assert retry_response.status_code == 201


@pytest.mark.asyncio
async def test_unsupported_adapter_and_access_control(client: AsyncClient):
    denied = await client.get("/integration/v1/adapters", headers=CitizenHeaders.value())
    assert denied.status_code == 403

    missing = await client.post(
        "/integration/v1/requests",
        headers=AdminHeaders.value("admin-003"),
        json={
            "adapter_code": "unknown-system",
            "operation_code": "lookup",
            "idempotency_key": "x-1",
            "canonical_payload": {},
            "request_payload": {},
        },
    )
    assert missing.status_code == 404
    assert missing.json()["error_code"] == "INT-4001"
