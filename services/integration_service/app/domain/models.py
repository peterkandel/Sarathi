from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IntegrationSystem(str, Enum):
    CITIZENSHIP_REGISTRY = "citizenship_registry"
    TAX_AUTHORITY = "tax_authority"
    PASSPORT_SYSTEM = "passport_system"
    PAYMENT_SYSTEM = "payment_system"


class IntegrationAdapterType(str, Enum):
    REST = "rest"
    SOAP = "soap"
    FILE = "file"
    EVENT = "event"
    HYBRID = "hybrid"


class IntegrationRequestStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTERED = "dead_lettered"


class CircuitBreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class IntegrationAttemptStatus(str, Enum):
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRY_SCHEDULED = "retry_scheduled"


class IntegrationEventPublicationStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


class IntegrationAdapter(Base, TimestampMixin):
    __tablename__ = "integration_adapters"
    __table_args__ = (UniqueConstraint("adapter_code", "deleted_at", name="uq_integration_adapters_code_deleted_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    adapter_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    adapter_name: Mapped[str] = mapped_column(String(255), nullable=False)
    system_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    adapter_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    auth_type: Mapped[str] = mapped_column(String(64), nullable=False, default="none")
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    max_retry_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    breaker_failure_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    breaker_reset_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    adapter_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    requests: Mapped[list[IntegrationRequest]] = relationship("IntegrationRequest", back_populates="adapter", cascade="all, delete-orphan")
    breaker: Mapped[IntegrationCircuitBreaker | None] = relationship("IntegrationCircuitBreaker", back_populates="adapter", cascade="all, delete-orphan", uselist=False)


class IntegrationRequest(Base, TimestampMixin):
    __tablename__ = "integration_requests"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    adapter_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("integration_adapters.id", ondelete="CASCADE"), nullable=False, index=True)
    system_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    operation_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    canonical_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    request_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    response_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=IntegrationRequestStatus.QUEUED.value, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    queue_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    adapter: Mapped[IntegrationAdapter] = relationship("IntegrationAdapter", back_populates="requests")
    attempts: Mapped[list[IntegrationAttempt]] = relationship("IntegrationAttempt", back_populates="request", cascade="all, delete-orphan")
    events: Mapped[list[IntegrationEvent]] = relationship("IntegrationEvent", back_populates="request", cascade="all, delete-orphan")


class IntegrationCircuitBreaker(Base, TimestampMixin):
    __tablename__ = "integration_circuit_breakers"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    adapter_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("integration_adapters.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default=CircuitBreakerState.CLOSED.value)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    half_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    reset_after_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    adapter: Mapped[IntegrationAdapter] = relationship("IntegrationAdapter", back_populates="breaker")


class IntegrationAttempt(Base, TimestampMixin):
    __tablename__ = "integration_attempts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("integration_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    adapter_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_class: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    response_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    request: Mapped[IntegrationRequest] = relationship("IntegrationRequest", back_populates="attempts")


class IntegrationEvent(Base, TimestampMixin):
    __tablename__ = "integration_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("integration_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    old_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    publication_status: Mapped[str] = mapped_column(String(32), nullable=False, default=IntegrationEventPublicationStatus.PENDING.value, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    channel: Mapped[str] = mapped_column(String(120), nullable=False, default="integration_bus")

    request: Mapped[IntegrationRequest] = relationship("IntegrationRequest", back_populates="events")
