from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditEvent(BaseModel):
    event_type: str
    actor_subject: str | None = None
    aggregate_id: UUID | None = None
    action: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    outcome: str | None = None
    payload: dict[str, object] = {}
    details: dict[str, object] = {}


class ApplicationHistoryEventCreate(BaseModel):
    event_type: str
    notes: str | None = None
    payload: dict[str, object] = {}
    recorded_by_subject: str | None = None
    recorded_at: datetime | None = None
