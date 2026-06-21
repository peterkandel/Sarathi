from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationTemplateCreate(BaseModel):
    template_code: str = Field(min_length=1, max_length=120)
    template_name: str = Field(min_length=1, max_length=255)
    channel: str = Field(min_length=1, max_length=32)
    version_number: int = Field(default=1, ge=1)
    subject_template: str | None = Field(default=None, max_length=255)
    body_template: str = Field(min_length=1)
    push_title_template: str | None = Field(default=None, max_length=255)
    push_body_template: str | None = None
    enabled: bool = True
    template_metadata: dict[str, object] = Field(default_factory=dict)


class NotificationTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    template_code: str
    template_name: str
    channel: str
    version_number: int
    subject_template: str | None
    body_template: str
    push_title_template: str | None
    push_body_template: str | None
    enabled: bool
    template_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class NotificationCreate(BaseModel):
    recipient_subject: str = Field(min_length=1, max_length=120)
    recipient_contact: str | None = Field(default=None, max_length=255)
    channel: str = Field(min_length=1, max_length=32)
    template_code: str
    template_version: int | None = Field(default=None, ge=1)
    category_code: str = Field(min_length=1, max_length=120)
    title: str | None = Field(default=None, max_length=255)
    context: dict[str, object] = Field(default_factory=dict)
    scheduled_for: datetime | None = None
    priority: int = Field(default=0, ge=0)
    max_retry_count: int = Field(default=3, ge=0)


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    template_id: UUID | None
    recipient_subject: str
    recipient_contact: str | None
    channel: str
    category_code: str
    title: str
    body: str
    rendered_context: dict[str, object]
    status: str
    priority: int
    scheduled_for: datetime | None
    sent_at: datetime | None
    delivered_at: datetime | None
    read_at: datetime | None
    archived_at: datetime | None
    retry_count: int
    max_retry_count: int
    next_retry_at: datetime | None
    last_error: str | None
    delivery_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class NotificationQueueItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notification_id: UUID
    channel: str
    status: str
    available_at: datetime
    attempt_count: int
    max_attempts: int
    locked_at: datetime | None
    processed_at: datetime | None
    next_retry_at: datetime | None
    last_error: str | None
    worker_id: str | None
    correlation_id: str | None
    created_at: datetime
    updated_at: datetime


class NotificationDeliveryAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notification_id: UUID
    queue_item_id: UUID
    channel: str
    attempt_no: int
    provider_name: str
    status: str
    provider_message_id: str | None
    error_code: str | None
    error_message: str | None
    request_payload: dict[str, object]
    response_payload: dict[str, object]
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class NotificationEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notification_id: UUID
    event_type: str
    old_status: str | None
    new_status: str | None
    actor_subject: str | None
    payload: dict[str, object]
    created_at: datetime
    updated_at: datetime


class NotificationSummary(BaseModel):
    total_notifications: int
    unread_count: int
    queued_count: int
    delivered_count: int
    failed_count: int


class QueueProcessResult(BaseModel):
    processed: int
    delivered: int
    failed: int
    retried: int


class MessageResponse(BaseModel):
    message: str
