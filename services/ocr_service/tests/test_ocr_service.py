from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.api.dependencies import get_ocr_provider, get_storage_service
from app.main import app


class StubStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def save(self, storage_key: str, content: bytes, mime_type: str) -> None:
        _ = mime_type
        self.objects[storage_key] = content

    async def load(self, storage_key: str) -> bytes:
        return self.objects[storage_key]


class StubEngine:
    async def preprocess(self, document):
        return type("Preprocessed", (), {"normalized_bytes": document.content.upper(), "quality_score": 0.92, "page_count": 1, "metadata": {"stub": True}})()

    async def recognize_text(self, document, document_type_code: str):
        _ = document_type_code
        return type("TextResult", (), {"text": "citizenship_number: ABC 123\nfull_name: Test Citizen\ndate_of_birth: 1990-01-01", "confidence": 0.96, "metadata": {"engine": "stub"}})()

    async def extract_fields(self, text_result, document_type_code: str):
        _ = text_result
        _ = document_type_code
        return [
            type("Field", (), {"field_name": "citizenship_number", "raw_value": "ABC 123", "normalized_value": "ABC123", "confidence": 0.97, "validation_status": "PASS", "source_language": "en"})(),
            type("Field", (), {"field_name": "full_name", "raw_value": "Test Citizen", "normalized_value": "Test Citizen", "confidence": 0.95, "validation_status": "PASS", "source_language": "en"})(),
        ]

    async def validate(self, fields, document_type_code: str):
        _ = fields
        _ = document_type_code
        return type("Validation", (), {"status": "PASS", "issues": []})()


def citizen_headers(subject: str = "citizen-001") -> dict[str, str]:
    return {
        "x-sarathi-subject": subject,
        "x-sarathi-roles": "Citizen",
        "x-sarathi-agency-id": "agency-01",
    }


def reviewer_headers(subject: str = "reviewer-001") -> dict[str, str]:
    return {
        "x-sarathi-subject": subject,
        "x-sarathi-roles": "Reviewer",
        "x-sarathi-agency-id": "agency-01",
    }


@pytest.fixture()
async def ocr_overrides():
    storage = StubStorage()
    engine = StubEngine()
    app.dependency_overrides[get_storage_service] = lambda: storage
    app.dependency_overrides[get_ocr_provider] = lambda: engine
    yield storage, engine
    app.dependency_overrides.pop(get_storage_service, None)
    app.dependency_overrides.pop(get_ocr_provider, None)


@pytest.mark.asyncio
async def test_job_upload_process_and_confidence(client: AsyncClient, ocr_overrides):
    storage, _ = ocr_overrides
    response = await client.post(
        "/ocr/v1/jobs",
        headers=citizen_headers(),
        files={"file": ("citizenship.png", b"fake citizenship image bytes", "image/png")},
        data={
            "document_id": str(uuid4()),
            "file_id": str(uuid4()),
            "document_type_code": "CITIZENSHIP_CERTIFICATE",
            "priority": "normal",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["document_confidence"] > 0.0

    job_id = body["id"]
    get_response = await client.get(f"/ocr/v1/jobs/{job_id}", headers=citizen_headers())
    assert get_response.status_code == 200
    assert get_response.json()["structured_output"]["validation_status"] == "PASS"

    confidence_response = await client.get(f"/ocr/v1/jobs/{job_id}/confidence", headers=reviewer_headers())
    assert confidence_response.status_code == 200
    confidence_body = confidence_response.json()
    assert confidence_body["risk_level"] == "low"
    assert len(confidence_body["field_confidences"]) >= 2

    assert len(storage.objects) >= 2


@pytest.mark.asyncio
async def test_reprocess_and_error_handling(client: AsyncClient, ocr_overrides):
    response = await client.post(
        "/ocr/v1/jobs",
        headers=citizen_headers("citizen-002"),
        files={"file": ("citizenship.png", b"fake citizenship image bytes", "image/png")},
        data={
            "document_id": str(uuid4()),
            "file_id": str(uuid4()),
            "document_type_code": "CITIZENSHIP_CERTIFICATE",
            "priority": "high",
        },
    )
    job_id = response.json()["id"]

    reprocess_response = await client.post(
        f"/ocr/v1/jobs/{job_id}/reprocess",
        headers=reviewer_headers(),
        json={"model_version": "future-model-v2", "force_human_review": True},
    )
    assert reprocess_response.status_code == 200
    assert reprocess_response.json()["status"] == "REVIEW_REQUIRED"

    unsupported_response = await client.post(
        "/ocr/v1/jobs",
        headers=citizen_headers("citizen-003"),
        files={"file": ("citizenship.txt", b"abc", "text/plain")},
        data={
            "document_id": str(uuid4()),
            "file_id": str(uuid4()),
            "document_type_code": "CITIZENSHIP_CERTIFICATE",
        },
    )
    assert unsupported_response.status_code == 400
    assert unsupported_response.json()["error_code"] == "OCR-4001"


@pytest.mark.asyncio
async def test_access_control_for_confidence(client: AsyncClient, ocr_overrides):
    response = await client.post(
        "/ocr/v1/jobs",
        headers=citizen_headers("citizen-004"),
        files={"file": ("citizenship.png", b"fake citizenship image bytes", "image/png")},
        data={
            "document_id": str(uuid4()),
            "file_id": str(uuid4()),
            "document_type_code": "CITIZENSHIP_CERTIFICATE",
        },
    )
    job_id = response.json()["id"]

    other_response = await client.get(f"/ocr/v1/jobs/{job_id}", headers=citizen_headers("citizen-999"))
    assert other_response.status_code == 403
