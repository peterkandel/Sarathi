from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApplicationCreate(BaseModel):
    workflow_definition_code: str = Field(min_length=1, max_length=120)
    workflow_definition_version: str = Field(min_length=1, max_length=32)
    entity_type: str = Field(min_length=1, max_length=120)
    entity_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    application_metadata: dict[str, object] = Field(default_factory=dict)


class ApplicationDocumentCreate(BaseModel):
    document_type: str = Field(min_length=1, max_length=64)
    file_name: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=255)
    storage_key: str = Field(min_length=1, max_length=255)
    checksum_sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    size_bytes: int = Field(ge=0)
    document_metadata: dict[str, object] = Field(default_factory=dict)


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reference_number: str
    applicant_subject: str
    workflow_definition_code: str
    workflow_definition_version: str
    entity_type: str
    entity_id: str
    title: str
    description: str | None
    application_status: str
    payload: dict[str, object]
    application_metadata: dict[str, object]
    workflow_application_id: UUID | None
    workflow_status: str | None
    workflow_current_state_id: UUID | None
    workflow_current_state_code: str | None
    submitted_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ApplicationDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    document_type: str
    file_name: str
    mime_type: str
    storage_key: str
    checksum_sha256: str
    size_bytes: int
    document_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class ApplicationStatusRead(BaseModel):
    application_id: UUID
    application_status: str
    workflow_application_id: UUID | None
    workflow_status: str | None
    workflow_current_state_id: UUID | None
    workflow_current_state_code: str | None
    submitted_at: datetime | None
    resolved_at: datetime | None
    document_count: int


class ApplicationHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    event_type: str
    notes: str | None
    payload: dict[str, object]
    recorded_by_subject: str | None
    recorded_at: datetime


class MessageResponse(BaseModel):
    message: str
