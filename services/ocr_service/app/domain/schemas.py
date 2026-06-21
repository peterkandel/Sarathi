from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OcrJobPriority(str, Enum):
    NORMAL = "normal"
    HIGH = "high"


class OcrJobCreateResponse(BaseModel):
    job_id: UUID
    status: str
    created_at: datetime


class OcrJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    file_id: UUID
    document_type_code: str
    priority: str
    status: str
    file_name: str
    mime_type: str
    original_storage_key: str
    normalized_storage_key: str | None
    model_name: str
    model_version: str
    pipeline_version: str
    document_confidence: float | None
    risk_score: float | None
    validation_status: str | None
    structured_output: dict[str, object]
    error_code: str | None
    error_message: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class OcrArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    stage: str
    artifact_type: str
    storage_key: str
    mime_type: str
    checksum_sha256: str
    size_bytes: int
    artifact_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class OcrJobConfidenceRead(BaseModel):
    job_id: UUID
    document_confidence: float
    preprocessing_confidence: float
    ocr_confidence: float
    validation_confidence: float
    risk_score: float
    risk_level: str
    model_name: str
    model_version: str
    field_confidences: list[dict[str, object]]


class OcrReprocessRequest(BaseModel):
    model_version: str | None = None
    force_human_review: bool = False


class OcrFieldOutput(BaseModel):
    field_name: str
    raw_value: str | None = None
    normalized_value: str | None = None
    confidence: float
    validation_status: str
    source_language: str | None = None


class OcrStructuredOutput(BaseModel):
    text: str
    page_count: int
    fields: list[OcrFieldOutput]
    validation_status: str
    validation_issues: list[dict[str, object]]
    document_confidence: float
    risk_score: float
    risk_level: str
    model_name: str
    model_version: str
    preprocessing: dict[str, object]
    raw_ocr: dict[str, object]


class OcrErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)
