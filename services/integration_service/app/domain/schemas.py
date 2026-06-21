from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IntegrationAdapterCreate(BaseModel):
    adapter_code: str = Field(min_length=1, max_length=120)
    adapter_name: str = Field(min_length=1, max_length=255)
    system_code: str = Field(min_length=1, max_length=120)
    adapter_type: str = Field(min_length=1, max_length=32)
    base_url: str | None = Field(default=None, max_length=512)
    auth_type: str = Field(default="none", max_length=64)
    timeout_seconds: int = Field(default=30, ge=1)
    max_retry_attempts: int = Field(default=3, ge=1)
    breaker_failure_threshold: int = Field(default=3, ge=1)
    breaker_reset_seconds: int = Field(default=60, ge=1)
    enabled: bool = True
    adapter_metadata: dict[str, object] = Field(default_factory=dict)


class IntegrationAdapterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    adapter_code: str
    adapter_name: str
    system_code: str
    adapter_type: str
    base_url: str | None
    auth_type: str
    timeout_seconds: int
    max_retry_attempts: int
    breaker_failure_threshold: int
    breaker_reset_seconds: int
    enabled: bool
    adapter_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class IntegrationRequestCreate(BaseModel):
    adapter_code: str = Field(min_length=1, max_length=120)
    operation_code: str = Field(min_length=1, max_length=120)
    idempotency_key: str = Field(min_length=1, max_length=120)
    correlation_id: str | None = Field(default=None, max_length=120)
    external_reference: str | None = Field(default=None, max_length=255)
    canonical_payload: dict[str, object] = Field(default_factory=dict)
    request_payload: dict[str, object] = Field(default_factory=dict)
    max_attempts: int = Field(default=3, ge=1)


class IntegrationRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    adapter_id: UUID
    system_code: str
    operation_code: str
    idempotency_key: str
    correlation_id: str | None
    external_reference: str | None
    canonical_payload: dict[str, object]
    request_payload: dict[str, object]
    response_payload: dict[str, object]
    status: str
    retry_count: int
    max_attempts: int
    next_retry_at: datetime | None
    last_error_code: str | None
    last_error_message: str | None
    sent_at: datetime | None
    completed_at: datetime | None
    failed_at: datetime | None
    published_at: datetime | None
    queue_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class IntegrationAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_id: UUID
    attempt_no: int
    status: str
    adapter_code: str
    provider_name: str
    http_status: int | None
    error_class: str | None
    error_code: str | None
    error_message: str | None
    request_payload: dict[str, object]
    response_payload: dict[str, object]
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class IntegrationEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_id: UUID
    event_type: str
    old_status: str | None
    new_status: str | None
    publication_status: str
    published_at: datetime | None
    payload: dict[str, object]
    channel: str
    created_at: datetime
    updated_at: datetime


class CircuitBreakerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    adapter_id: UUID
    state: str
    failure_count: int
    success_count: int
    opened_at: datetime | None
    half_opened_at: datetime | None
    last_failure_at: datetime | None
    last_error_code: str | None
    last_error_message: str | None
    reset_after_seconds: int
    created_at: datetime
    updated_at: datetime


class QueueProcessResult(BaseModel):
    processed: int
    completed: int
    failed: int
    retried: int


class PublishResult(BaseModel):
    published: int


class MessageResponse(BaseModel):
    message: str
