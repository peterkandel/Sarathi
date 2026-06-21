from __future__ import annotations

import pytest
from httpx import AsyncClient


class CitizenHeaders:
    @staticmethod
    def value(subject: str = "citizen-001") -> dict[str, str]:
        return {
            "x-sarathi-subject": subject,
            "x-sarathi-roles": "Citizen",
            "x-sarathi-agency-id": "agency-01",
        }


class AdminHeaders:
    @staticmethod
    def value(subject: str = "admin-001") -> dict[str, str]:
        return {
            "x-sarathi-subject": subject,
            "x-sarathi-roles": "Administrator",
            "x-sarathi-agency-id": "agency-01",
        }


@pytest.mark.asyncio
async def test_template_notification_delivery_and_tracking(client: AsyncClient):
    template_response = await client.post(
        "/notifications/v1/templates",
        headers=AdminHeaders.value(),
        json={
            "template_code": "application_update",
            "template_name": "Application Update",
            "channel": "email",
            "subject_template": "Application update for {recipient_subject}",
            "body_template": "Hello {recipient_subject}, your case {case_number} is now {status}.",
            "template_metadata": {"source": "workflow"},
        },
    )
    assert template_response.status_code == 201
    template_id = template_response.json()["id"]

    notification_response = await client.post(
        "/notifications/v1/notifications",
        headers=AdminHeaders.value(),
        json={
            "recipient_subject": "citizen-001",
            "recipient_contact": "citizen@example.com",
            "channel": "email",
            "template_code": "application_update",
            "category_code": "application",
            "context": {"case_number": "APP-001", "status": "approved"},
        },
    )
    assert notification_response.status_code == 201
    notification = notification_response.json()
    assert notification["template_id"] == template_id
    assert "APP-001" in notification["body"]

    queue_response = await client.post("/notifications/v1/queue/process", headers=AdminHeaders.value(), json={"limit": 10})
    assert queue_response.status_code == 200
    assert queue_response.json()["delivered"] == 1

    delivery_response = await client.get(f"/notifications/v1/notifications/{notification['id']}/attempts", headers=CitizenHeaders.value())
    assert delivery_response.status_code == 200
    assert len(delivery_response.json()) == 1
    assert delivery_response.json()[0]["status"] == "delivered"

    fetched_response = await client.get(f"/notifications/v1/notifications/{notification['id']}", headers=CitizenHeaders.value())
    assert fetched_response.status_code == 200
    assert fetched_response.json()["status"] == "delivered"


@pytest.mark.asyncio
async def test_retry_handling_and_inbox_access_control(client: AsyncClient):
    await client.post(
        "/notifications/v1/templates",
        headers=AdminHeaders.value("admin-002"),
        json={
            "template_code": "payment_reminder",
            "template_name": "Payment Reminder",
            "channel": "sms",
            "subject_template": "Reminder",
            "body_template": "Payment reminder for {recipient_subject}",
        },
    )

    create_response = await client.post(
        "/notifications/v1/notifications",
        headers=AdminHeaders.value("admin-002"),
        json={
            "recipient_subject": "citizen-002",
            "recipient_contact": "+9779800000000",
            "channel": "sms",
            "template_code": "payment_reminder",
            "category_code": "payments",
            "context": {"simulate_failure_attempts": 1},
            "max_retry_count": 2,
        },
    )
    assert create_response.status_code == 201
    notification_id = create_response.json()["id"]

    first_process = await client.post("/notifications/v1/queue/process", headers=AdminHeaders.value("admin-002"), json={"limit": 10})
    assert first_process.status_code == 200
    assert first_process.json()["retried"] == 1

    second_process = await client.post("/notifications/v1/queue/process", headers=AdminHeaders.value("admin-002"), json={"limit": 10})
    assert second_process.status_code == 200
    assert second_process.json()["delivered"] == 1

    citizen_view = await client.get("/notifications/v1/notifications", headers=CitizenHeaders.value("citizen-002"))
    assert citizen_view.status_code == 200
    assert len(citizen_view.json()) == 1

    unread_response = await client.get("/notifications/v1/unread-count", headers=CitizenHeaders.value("citizen-002"))
    assert unread_response.status_code == 200
    assert unread_response.json()["unread_count"] == 1

    mark_read = await client.post(f"/notifications/v1/notifications/{notification_id}/read", headers=CitizenHeaders.value("citizen-002"))
    assert mark_read.status_code == 200
    assert mark_read.json()["status"] == "read"

    archive = await client.post(f"/notifications/v1/notifications/{notification_id}/archive", headers=CitizenHeaders.value("citizen-002"))
    assert archive.status_code == 200
    assert archive.json()["status"] == "archived"


@pytest.mark.asyncio
async def test_channel_support_and_summary(client: AsyncClient):
    for channel in ("push", "email"):
        await client.post(
            "/notifications/v1/templates",
            headers=AdminHeaders.value("admin-003"),
            json={
                "template_code": f"status_{channel}",
                "template_name": f"Status {channel.title()}",
                "channel": channel,
                "subject_template": "Status update",
                "body_template": "{channel} update for {recipient_subject}",
            },
        )
        await client.post(
            "/notifications/v1/notifications",
            headers=AdminHeaders.value("admin-003"),
            json={
                "recipient_subject": "citizen-003",
                "recipient_contact": "citizen@example.com",
                "channel": channel,
                "template_code": f"status_{channel}",
                "category_code": "status",
                "context": {"channel": channel},
            },
        )

    process_response = await client.post("/notifications/v1/queue/process", headers=AdminHeaders.value("admin-003"), json={"limit": 10})
    assert process_response.status_code == 200
    assert process_response.json()["processed"] == 2

    summary_response = await client.get("/notifications/v1/summary", headers=CitizenHeaders.value("citizen-003"))
    assert summary_response.status_code == 200
    assert summary_response.json()["total_notifications"] == 2
