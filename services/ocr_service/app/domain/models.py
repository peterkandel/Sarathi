from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Uuid
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


class OcrJobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class OcrRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class OcrArtifactStage(str, Enum):
    UPLOAD = "upload"
    PREPROCESSING = "preprocessing"
    OCR = "ocr"
    EXTRACTION = "extraction"
    VALIDATION = "validation"


class OcrJob(Base, TimestampMixin, AuditMixin):
    __tablename__ = "ocr_jobs"
    __table_args__ = (UniqueConstraint("document_id", "file_id", "deleted_at", name="uq_ocr_jobs_document_file_deleted_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    file_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    document_type_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="normal")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=OcrJobStatus.QUEUED.value)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    original_storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False, default="heuristic")
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, default="heuristic-v1")
    pipeline_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0")
    document_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    structured_output: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    artifacts: Mapped[list[OcrJobArtifact]] = relationship("OcrJobArtifact", back_populates="job", cascade="all, delete-orphan")
    events: Mapped[list[OcrJobEvent]] = relationship("OcrJobEvent", back_populates="job", cascade="all, delete-orphan", order_by="OcrJobEvent.recorded_at")


class OcrJobArtifact(Base, TimestampMixin):
    __tablename__ = "ocr_job_artifacts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("ocr_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    artifact_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    job: Mapped[OcrJob] = relationship("OcrJob", back_populates="artifacts")


class OcrJobEvent(Base, TimestampMixin):
    __tablename__ = "ocr_job_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("ocr_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    stage: Mapped[str | None] = mapped_column(String(32), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    job: Mapped[OcrJob] = relationship("OcrJob", back_populates="events")
