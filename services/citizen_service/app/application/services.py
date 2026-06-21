from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status

from app.domain.events import AuditEvent
from app.domain.models import CitizenProfile, CitizenshipRecord, DocumentMetadata, CitizenshipStatus, DocumentStatus, ProfileStatus
from app.domain.schemas import (
    CitizenProfileCreate,
    CitizenProfileUpdate,
    CitizenshipRecordCreate,
    CitizenshipRecordUpdate,
    DocumentMetadataCreate,
    DocumentMetadataUpdate,
)
from app.infrastructure.repositories import AuditRepository, CitizenProfileRepository, CitizenshipRecordRepository, DocumentMetadataRepository
from shared_auth import Role
from shared_auth.security import has_any_role
from shared_auth.models import Principal


ELEVATED_ROLES = (
    Role.CLERK,
    Role.REVIEWER,
    Role.MANAGER,
    Role.ADMINISTRATOR,
    Role.SUPER_ADMINISTRATOR,
)


class CitizenService:
    def __init__(
        self,
        profile_repository: CitizenProfileRepository,
        record_repository: CitizenshipRecordRepository,
        document_repository: DocumentMetadataRepository,
        audit_repository: AuditRepository,
    ) -> None:
        self.profiles = profile_repository
        self.records = record_repository
        self.documents = document_repository
        self.audit = audit_repository

    def _is_privileged(self, principal: Principal) -> bool:
        return has_any_role(principal, ELEVATED_ROLES)

    def _ensure_profile_access(self, principal: Principal, profile: CitizenProfile) -> None:
        if principal.subject != profile.identity_subject and not self._is_privileged(principal):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Profile access denied")

    def _ensure_profile_write_access(self, principal: Principal, target_subject: str) -> None:
        if principal.subject != target_subject and not self._is_privileged(principal):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Profile write denied")

    async def create_profile(self, payload: CitizenProfileCreate, principal: Principal) -> CitizenProfile:
        target_subject = payload.identity_subject or principal.subject
        self._ensure_profile_write_access(principal, target_subject)
        existing_profile = await self.profiles.get_profile_by_identity_subject(target_subject)
        if existing_profile is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profile already exists")

        profile = CitizenProfile(
            identity_subject=target_subject,
            full_name=payload.full_name,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender.value if payload.gender else None,
            email=payload.email.lower() if payload.email else None,
            phone_number=payload.phone_number,
            primary_language=payload.primary_language,
            current_address=payload.current_address,
            permanent_address=payload.permanent_address,
            profile_status=payload.profile_status.value,
            profile_metadata=payload.profile_metadata,
            created_by_subject=principal.subject,
            updated_by_subject=principal.subject,
        )
        created_profile = await self.profiles.create_profile(profile)
        await self.audit.record_event(
            AuditEvent(
                event_type="CitizenProfileCreated",
                actor_subject=principal.subject,
                aggregate_id=created_profile.id,
                action="create_profile",
                resource_type="citizen_profile",
                resource_id=str(created_profile.id),
                outcome="success",
                payload={"identity_subject": created_profile.identity_subject},
                details={"profile_status": created_profile.profile_status},
            )
        )
        return created_profile

    async def get_profile_by_id(self, profile_id: UUID, principal: Principal) -> CitizenProfile:
        profile = await self.profiles.get_profile_by_id(profile_id)
        if profile is None or profile.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        self._ensure_profile_access(principal, profile)
        return profile

    async def get_profile_by_identity_subject(self, identity_subject: str, principal: Principal) -> CitizenProfile:
        profile = await self.profiles.get_profile_by_identity_subject(identity_subject)
        if profile is None or profile.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        self._ensure_profile_access(principal, profile)
        return profile

    async def list_profiles(self, principal: Principal) -> list[CitizenProfile]:
        if not self._is_privileged(principal):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Profile listing denied")
        return list(await self.profiles.list_profiles())

    async def update_profile(self, profile_id: UUID, payload: CitizenProfileUpdate, principal: Principal) -> CitizenProfile:
        profile = await self.get_profile_by_id(profile_id, principal)
        update_data = payload.model_dump(exclude_unset=True)
        if "email" in update_data and update_data["email"] is not None:
            update_data["email"] = update_data["email"].lower()
        if "gender" in update_data and update_data["gender"] is not None:
            update_data["gender"] = update_data["gender"].value
        if "profile_status" in update_data and update_data["profile_status"] is not None:
            update_data["profile_status"] = update_data["profile_status"].value
        for field_name, field_value in update_data.items():
            setattr(profile, field_name, field_value)
        profile.updated_by_subject = principal.subject
        updated_profile = await self.profiles.update_profile(profile)
        await self.audit.record_event(
            AuditEvent(
                event_type="CitizenProfileUpdated",
                actor_subject=principal.subject,
                aggregate_id=updated_profile.id,
                action="update_profile",
                resource_type="citizen_profile",
                resource_id=str(updated_profile.id),
                outcome="success",
                payload=update_data,
                details={"profile_status": updated_profile.profile_status},
            )
        )
        return updated_profile

    async def delete_profile(self, profile_id: UUID, principal: Principal) -> CitizenProfile:
        profile = await self.get_profile_by_id(profile_id, principal)
        profile.deleted_at = datetime.now(timezone.utc)
        profile.updated_by_subject = principal.subject
        deleted_profile = await self.profiles.update_profile(profile)
        await self.audit.record_event(
            AuditEvent(
                event_type="CitizenProfileDeleted",
                actor_subject=principal.subject,
                aggregate_id=deleted_profile.id,
                action="delete_profile",
                resource_type="citizen_profile",
                resource_id=str(deleted_profile.id),
                outcome="success",
                payload={},
                details={},
            )
        )
        return deleted_profile

    async def create_record(self, profile_id: UUID, payload: CitizenshipRecordCreate, principal: Principal) -> CitizenshipRecord:
        profile = await self.get_profile_by_id(profile_id, principal)
        record = CitizenshipRecord(
            profile_id=profile.id,
            certificate_number=payload.certificate_number,
            status=payload.status.value,
            issued_on=payload.issued_on,
            issuing_office=payload.issuing_office,
            valid_from=payload.valid_from,
            valid_until=payload.valid_until,
            notes=payload.notes,
            record_metadata=payload.record_metadata,
            created_by_subject=principal.subject,
            updated_by_subject=principal.subject,
        )
        created_record = await self.records.create_record(record)
        await self.audit.record_event(
            AuditEvent(
                event_type="CitizenshipRecordCreated",
                actor_subject=principal.subject,
                aggregate_id=created_record.id,
                action="create_record",
                resource_type="citizenship_record",
                resource_id=str(created_record.id),
                outcome="success",
                payload={"profile_id": str(profile.id), "certificate_number": created_record.certificate_number},
                details={"status": created_record.status},
            )
        )
        return created_record

    async def list_records(self, profile_id: UUID, principal: Principal) -> list[CitizenshipRecord]:
        await self.get_profile_by_id(profile_id, principal)
        return list(await self.records.list_records_for_profile(profile_id))

    async def get_record(self, record_id: UUID, principal: Principal) -> CitizenshipRecord:
        record = await self.records.get_record_by_id(record_id)
        if record is None or record.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
        await self.get_profile_by_id(record.profile_id, principal)
        return record

    async def update_record(self, record_id: UUID, payload: CitizenshipRecordUpdate, principal: Principal) -> CitizenshipRecord:
        record = await self.get_record(record_id, principal)
        update_data = payload.model_dump(exclude_unset=True)
        if "status" in update_data and update_data["status"] is not None:
            update_data["status"] = update_data["status"].value
        for field_name, field_value in update_data.items():
            setattr(record, field_name, field_value)
        record.updated_by_subject = principal.subject
        updated_record = await self.records.update_record(record)
        await self.audit.record_event(
            AuditEvent(
                event_type="CitizenshipRecordUpdated",
                actor_subject=principal.subject,
                aggregate_id=updated_record.id,
                action="update_record",
                resource_type="citizenship_record",
                resource_id=str(updated_record.id),
                outcome="success",
                payload=update_data,
                details={"profile_id": str(updated_record.profile_id)},
            )
        )
        return updated_record

    async def delete_record(self, record_id: UUID, principal: Principal) -> CitizenshipRecord:
        record = await self.get_record(record_id, principal)
        revoked_record = await self.records.revoke_record(record.id, datetime.now(timezone.utc))
        if revoked_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
        await self.audit.record_event(
            AuditEvent(
                event_type="CitizenshipRecordDeleted",
                actor_subject=principal.subject,
                aggregate_id=revoked_record.id,
                action="delete_record",
                resource_type="citizenship_record",
                resource_id=str(revoked_record.id),
                outcome="success",
                payload={},
                details={"profile_id": str(revoked_record.profile_id)},
            )
        )
        return revoked_record

    async def create_document(self, profile_id: UUID, payload: DocumentMetadataCreate, principal: Principal) -> DocumentMetadata:
        profile = await self.get_profile_by_id(profile_id, principal)
        document = DocumentMetadata(
            profile_id=profile.id,
            document_type=payload.document_type.value,
            file_name=payload.file_name,
            mime_type=payload.mime_type,
            storage_key=payload.storage_key,
            checksum_sha256=payload.checksum_sha256.lower(),
            size_bytes=payload.size_bytes,
            document_status=payload.document_status.value,
            verified_at=payload.verified_at,
            verified_by_subject=payload.verified_by_subject,
            rejection_reason=payload.rejection_reason,
            document_metadata=payload.document_metadata,
            created_by_subject=principal.subject,
            updated_by_subject=principal.subject,
        )
        created_document = await self.documents.create_document(document)
        await self.audit.record_event(
            AuditEvent(
                event_type="DocumentMetadataCreated",
                actor_subject=principal.subject,
                aggregate_id=created_document.id,
                action="create_document",
                resource_type="document_metadata",
                resource_id=str(created_document.id),
                outcome="success",
                payload={"profile_id": str(profile.id), "document_type": created_document.document_type},
                details={"storage_key": created_document.storage_key},
            )
        )
        return created_document

    async def list_documents(self, profile_id: UUID, principal: Principal) -> list[DocumentMetadata]:
        await self.get_profile_by_id(profile_id, principal)
        return list(await self.documents.list_documents_for_profile(profile_id))

    async def get_document(self, document_id: UUID, principal: Principal) -> DocumentMetadata:
        document = await self.documents.get_document_by_id(document_id)
        if document is None or document.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        await self.get_profile_by_id(document.profile_id, principal)
        return document

    async def update_document(self, document_id: UUID, payload: DocumentMetadataUpdate, principal: Principal) -> DocumentMetadata:
        document = await self.get_document(document_id, principal)
        update_data = payload.model_dump(exclude_unset=True)
        if "document_type" in update_data and update_data["document_type"] is not None:
            update_data["document_type"] = update_data["document_type"].value
        if "document_status" in update_data and update_data["document_status"] is not None:
            update_data["document_status"] = update_data["document_status"].value
        if "checksum_sha256" in update_data and update_data["checksum_sha256"] is not None:
            update_data["checksum_sha256"] = update_data["checksum_sha256"].lower()
        for field_name, field_value in update_data.items():
            setattr(document, field_name, field_value)
        document.updated_by_subject = principal.subject
        updated_document = await self.documents.update_document(document)
        await self.audit.record_event(
            AuditEvent(
                event_type="DocumentMetadataUpdated",
                actor_subject=principal.subject,
                aggregate_id=updated_document.id,
                action="update_document",
                resource_type="document_metadata",
                resource_id=str(updated_document.id),
                outcome="success",
                payload=update_data,
                details={"profile_id": str(updated_document.profile_id)},
            )
        )
        return updated_document

    async def delete_document(self, document_id: UUID, principal: Principal) -> DocumentMetadata:
        document = await self.get_document(document_id, principal)
        deleted_document = await self.documents.delete_document(document.id, datetime.now(timezone.utc))
        if deleted_document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        await self.audit.record_event(
            AuditEvent(
                event_type="DocumentMetadataDeleted",
                actor_subject=principal.subject,
                aggregate_id=deleted_document.id,
                action="delete_document",
                resource_type="document_metadata",
                resource_id=str(deleted_document.id),
                outcome="success",
                payload={},
                details={"profile_id": str(deleted_document.profile_id)},
            )
        )
        return deleted_document