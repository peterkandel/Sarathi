from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OcrErrorPayload(BaseModel):
    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class OcrJobEventPayload(BaseModel):
    event_type: str
    stage: str | None = None
    message: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    recorded_at: datetime | None = None


class AuditEvent(BaseModel):
    event_type: str
    actor_subject: str | None = None
    aggregate_id: UUID | None = None
    action: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    outcome: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    details: dict[str, object] = Field(default_factory=dict)
