from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventMetadata(BaseModel):
    correlation_id: str | None = None
    causation_id: str | None = None
    trace_id: str | None = None
    source: str | None = None


class DomainEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    aggregate_id: str
    aggregate_type: str | None = None
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: EventMetadata = Field(default_factory=EventMetadata)


class IntegrationEvent(DomainEvent):
    source_service: str | None = None
    destination_service: str | None = None


class EventEnvelope(BaseModel):
    event: DomainEvent
    schema_version: int = 1
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
