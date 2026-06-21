from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from email_validator import validate_email
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


class CitizenProfileBase(BaseModel):
    identity_subject: str | None = Field(default=None, max_length=120)
    full_name: str = Field(min_length=1, max_length=255)
    date_of_birth: date
    gender: Gender | None = None
    email: str | None = Field(default=None, max_length=255)
    phone_number: str | None = Field(default=None, max_length=32)
    primary_language: str | None = Field(default=None, max_length=64)
    current_address: str | None = Field(default=None, max_length=500)
    permanent_address: str | None = Field(default=None, max_length=500)
    profile_status: ProfileStatus = ProfileStatus.ACTIVE
    profile_metadata: dict[str, object] = Field(default_factory=dict)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date) -> date:
        if value >= date.today():
            raise ValueError("date_of_birth must be in the past")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        validate_email(value, check_deliverability=False)
        return value.lower()


class CitizenProfileCreate(CitizenProfileBase):
    pass


class CitizenProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    date_of_birth: date | None = None
    gender: Gender | None = None
    email: str | None = Field(default=None, max_length=255)
    phone_number: str | None = Field(default=None, max_length=32)
    primary_language: str | None = Field(default=None, max_length=64)
    current_address: str | None = Field(default=None, max_length=500)
    permanent_address: str | None = Field(default=None, max_length=500)
    profile_status: ProfileStatus | None = None
    profile_metadata: dict[str, object] | None = None

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date | None) -> date | None:
        if value is not None and value >= date.today():
            raise ValueError("date_of_birth must be in the past")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        validate_email(value, check_deliverability=False)
        return value.lower()


class CitizenProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    identity_subject: str
    full_name: str
    date_of_birth: date
    gender: str | None
    email: str | None
    phone_number: str | None
    primary_language: str | None
    current_address: str | None
    permanent_address: str | None
    profile_status: str
    profile_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class CitizenshipRecordBase(BaseModel):
    certificate_number: str = Field(min_length=1, max_length=120)
    status: CitizenshipStatus = CitizenshipStatus.ACTIVE
    issued_on: date
    issuing_office: str = Field(min_length=1, max_length=255)
    valid_from: date | None = None
    valid_until: date | None = None
    notes: str | None = Field(default=None, max_length=2000)
    record_metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_validity_window(self) -> "CitizenshipRecordBase":
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("valid_until must be on or after valid_from")
        return self


class CitizenshipRecordCreate(CitizenshipRecordBase):
    pass


class CitizenshipRecordUpdate(BaseModel):
    certificate_number: str | None = Field(default=None, min_length=1, max_length=120)
    status: CitizenshipStatus | None = None
    issued_on: date | None = None
    issuing_office: str | None = Field(default=None, min_length=1, max_length=255)
    valid_from: date | None = None
    valid_until: date | None = None
    notes: str | None = Field(default=None, max_length=2000)
    record_metadata: dict[str, object] | None = None

    @model_validator(mode="after")
    def validate_validity_window(self) -> "CitizenshipRecordUpdate":
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("valid_until must be on or after valid_from")
        return self


class CitizenshipRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    certificate_number: str
    status: str
    issued_on: date
    issuing_office: str
    valid_from: date | None
    valid_until: date | None
    notes: str | None
    record_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class DocumentMetadataBase(BaseModel):
    document_type: DocumentType
    file_name: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=255)
    storage_key: str = Field(min_length=1, max_length=255)
    checksum_sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    size_bytes: int = Field(ge=0)
    document_status: DocumentStatus = DocumentStatus.UPLOADED
    verified_at: datetime | None = None
    verified_by_subject: str | None = Field(default=None, max_length=120)
    rejection_reason: str | None = Field(default=None, max_length=2000)
    document_metadata: dict[str, object] = Field(default_factory=dict)


class DocumentMetadataCreate(DocumentMetadataBase):
    pass


class DocumentMetadataUpdate(BaseModel):
    document_type: DocumentType | None = None
    file_name: str | None = Field(default=None, min_length=1, max_length=255)
    mime_type: str | None = Field(default=None, min_length=1, max_length=255)
    storage_key: str | None = Field(default=None, min_length=1, max_length=255)
    checksum_sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    size_bytes: int | None = Field(default=None, ge=0)
    document_status: DocumentStatus | None = None
    verified_at: datetime | None = None
    verified_by_subject: str | None = Field(default=None, max_length=120)
    rejection_reason: str | None = Field(default=None, max_length=2000)
    document_metadata: dict[str, object] | None = None


class DocumentMetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    document_type: str
    file_name: str
    mime_type: str
    storage_key: str
    checksum_sha256: str
    size_bytes: int
    document_status: str
    verified_at: datetime | None
    verified_by_subject: str | None
    rejection_reason: str | None
    document_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str