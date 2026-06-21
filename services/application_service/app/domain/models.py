from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditMixin:
    created_by_subject: Mapped[str | None] = mapped_column(String(120), nullable=True)
    updated_by_subject: Mapped[str | None] = mapped_column(String(120), nullable=True)


class ApplicationStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    COMPLETED = "COMPLETED"


class Application(Base, TimestampMixin, AuditMixin):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("reference_number", "deleted_at", name="uq_applications_reference_number_deleted_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    reference_number: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    applicant_subject: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    workflow_definition_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    workflow_definition_version: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    application_status: Mapped[str] = mapped_column(String(32), nullable=False, default=ApplicationStatus.DRAFT.value)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    application_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    workflow_application_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    workflow_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    workflow_current_state_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    workflow_current_state_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    documents: Mapped[list[ApplicationDocument]] = relationship("ApplicationDocument", back_populates="application", cascade="all, delete-orphan")
    history_events: Mapped[list[ApplicationHistoryEvent]] = relationship("ApplicationHistoryEvent", back_populates="application", cascade="all, delete-orphan", order_by="ApplicationHistoryEvent.recorded_at")


class ApplicationDocument(Base, TimestampMixin, AuditMixin):
    __tablename__ = "application_documents"
    __table_args__ = (UniqueConstraint("application_id", "storage_key", "deleted_at", name="uq_application_documents_application_storage_deleted_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    document_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    application: Mapped[Application] = relationship("Application", back_populates="documents")


class ApplicationHistoryEvent(Base, TimestampMixin):
    __tablename__ = "application_history_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    recorded_by_subject: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    application: Mapped[Application] = relationship("Application", back_populates="history_events")
