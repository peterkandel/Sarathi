from __future__ import annotations

from datetime import datetime, timezone
from logging import Logger, getLogger
from uuid import uuid4

from pydantic import BaseModel, Field

from .models import Principal


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    actor_subject: str | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    outcome: str
    details: dict[str, object] = Field(default_factory=dict)


class AuditLogger:
    def __init__(self, logger: Logger | None = None) -> None:
        self._logger = logger or getLogger("sarathi.audit")

    def log(self, event: AuditEvent) -> None:
        self._logger.info(event.model_dump_json())


def build_audit_event(
    *,
    event_type: str,
    action: str,
    outcome: str,
    principal: Principal | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict[str, object] | None = None,
) -> AuditEvent:
    return AuditEvent(
        event_type=event_type,
        actor_subject=principal.subject if principal else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
        details=details or {},
    )