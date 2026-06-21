from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class WorkflowClientError(RuntimeError):
    pass


class WorkflowServiceClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or settings.workflow_service_url

    async def submit_application(
        self,
        *,
        definition_code: str,
        definition_version: str,
        entity_type: str,
        entity_id: str,
        title: str,
        payload: dict[str, object],
        application_metadata: dict[str, object],
        applicant_subject: str,
    ) -> dict[str, object]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.post(
                "/api/v1/applications/submit",
                headers={"x-sarathi-subject": applicant_subject, "x-sarathi-roles": "Citizen", "x-sarathi-agency-id": "agency-01"},
                json={
                    "definition_code": definition_code,
                    "definition_version": definition_version,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "title": title,
                    "payload": payload,
                    "application_metadata": application_metadata,
                },
            )
        if response.status_code >= 400:
            raise WorkflowClientError(response.text)
        return response.json()

    async def get_application(self, workflow_application_id: str) -> dict[str, object]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.get(f"/api/v1/applications/{workflow_application_id}", headers={"x-sarathi-subject": "system", "x-sarathi-roles": "Administrator", "x-sarathi-agency-id": "agency-01"})
        if response.status_code >= 400:
            raise WorkflowClientError(response.text)
        return response.json()
