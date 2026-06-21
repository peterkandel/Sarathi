from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class IntegrationEventPayload(BaseModel):
    request_id: UUID
    event_type: str
    old_status: str | None = None
    new_status: str | None = None
    publication_status: str = "pending"
    channel: str = "integration_bus"
    payload: dict[str, object] = Field(default_factory=dict)


class IntegrationErrorPayload(BaseModel):
    error_code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class CircuitBreakerSnapshot(BaseModel):
    state: str
    failure_count: int
    success_count: int
    last_error_code: str | None = None
    last_error_message: str | None = None
