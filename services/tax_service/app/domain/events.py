from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TaxAuditEventPayload(BaseModel):
    event_type: str
    actor_subject: str | None = None
    aggregate_id: UUID | None = None
    action: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    outcome: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    details: dict[str, object] = Field(default_factory=dict)
    correlation_id: str | None = None


class CalculationTraceEntry(BaseModel):
    step: str
    description: str
    amount: float | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class ValidationIssue(BaseModel):
    code: str
    field_name: str | None = None
    message: str
    severity: str


class TaxErrorPayload(BaseModel):
    error_code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)
