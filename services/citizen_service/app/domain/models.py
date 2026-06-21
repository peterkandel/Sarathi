from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
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


class ProfileStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class Gender(str, Enum):
    FEMALE = "FEMALE"
    MALE = "MALE"
    OTHER = "OTHER"
    UNSPECIFIED = "UNSPECIFIED"


class CitizenshipStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class DocumentType(str, Enum):
    CITIZENSHIP_CERTIFICATE = "CITIZENSHIP_CERTIFICATE"
    BIRTH_CERTIFICATE = "BIRTH_CERTIFICATE"
    PASSPORT_PHOTO = "PASSPORT_PHOTO"
    PROOF_OF_ADDRESS = "PROOF_OF_ADDRESS"
    OTHER = "OTHER"


class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class CitizenProfile(Base, TimestampMixin, AuditMixin):
    __tablename__ = "citizen_profiles"
    __table_args__ = (UniqueConstraint("identity_subject", "deleted_at", name="uq_citizen_profiles_identity_subject_deleted_at"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    identity_subject: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    primary_language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    permanent_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    profile_status: Mapped[str] = mapped_column(String(32), nullable=False, default=ProfileStatus.ACTIVE.value)
    profile_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    citizenship_records: Mapped[list[CitizenshipRecord]] = relationship("CitizenshipRecord", back_populates="profile", cascade="all, delete-orphan")
    documents: Mapped[list[DocumentMetadata]] = relationship("DocumentMetadata", back_populates="profile", cascade="all, delete-orphan")


class CitizenshipRecord(Base, TimestampMixin, AuditMixin):
    __tablename__ = "citizenship_records"
    __table_args__ = (UniqueConstraint("certificate_number", "deleted_at", name="uq_citizenship_records_certificate_number_deleted_at"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("citizen_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    certificate_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=CitizenshipStatus.ACTIVE.value)
    issued_on: Mapped[date] = mapped_column(Date, nullable=False)
    issuing_office: Mapped[str] = mapped_column(String(255), nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    record_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    profile: Mapped[CitizenProfile] = relationship("CitizenProfile", back_populates="citizenship_records")


class DocumentMetadata(Base, TimestampMixin, AuditMixin):
    __tablename__ = "document_metadata"
    __table_args__ = (UniqueConstraint("storage_key", "deleted_at", name="uq_document_metadata_storage_key_deleted_at"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("citizen_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    document_status: Mapped[str] = mapped_column(String(32), nullable=False, default=DocumentStatus.UPLOADED.value)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_subject: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    profile: Mapped[CitizenProfile] = relationship("CitizenProfile", back_populates="documents")


class AuditEvent(Base, TimestampMixin):
    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    actor_subject: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    aggregate_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    action: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    details: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    correlation_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)