from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class NotificationEventPayload(BaseModel):
    notification_id: UUID
    event_type: str
    old_status: str | None = None
    new_status: str | None = None
    actor_subject: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
