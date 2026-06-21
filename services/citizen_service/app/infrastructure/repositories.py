from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import AuditEvent
from app.domain.models import AuditEvent as AuditEventModel
from app.domain.models import CitizenProfile, CitizenshipRecord, DocumentMetadata


class CitizenProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_profile(self, profile: CitizenProfile) -> CitizenProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def update_profile(self, profile: CitizenProfile) -> CitizenProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def get_profile_by_id(self, profile_id: UUID) -> CitizenProfile | None:
        statement = select(CitizenProfile).where(CitizenProfile.id == profile_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_profile_by_identity_subject(self, identity_subject: str) -> CitizenProfile | None:
        statement = select(CitizenProfile).where(CitizenProfile.identity_subject == identity_subject)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_profiles(self) -> Sequence[CitizenProfile]:
        statement = select(CitizenProfile).where(CitizenProfile.deleted_at.is_(None)).order_by(CitizenProfile.created_at.desc())
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class CitizenshipRecordRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_record(self, record: CitizenshipRecord) -> CitizenshipRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def update_record(self, record: CitizenshipRecord) -> CitizenshipRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_record_by_id(self, record_id: UUID) -> CitizenshipRecord | None:
        statement = select(CitizenshipRecord).where(CitizenshipRecord.id == record_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_records_for_profile(self, profile_id: UUID) -> Sequence[CitizenshipRecord]:
        statement = select(CitizenshipRecord).where(CitizenshipRecord.profile_id == profile_id, CitizenshipRecord.deleted_at.is_(None)).order_by(CitizenshipRecord.created_at.desc())
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def revoke_record(self, record_id: UUID, revoked_at: datetime) -> CitizenshipRecord | None:
        record = await self.get_record_by_id(record_id)
        if record is None:
            return None
        record.deleted_at = revoked_at
        await self.session.flush()
        return record


class DocumentMetadataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_document(self, document: DocumentMetadata) -> DocumentMetadata:
        self.session.add(document)
        await self.session.flush()
        return document

    async def update_document(self, document: DocumentMetadata) -> DocumentMetadata:
        self.session.add(document)
        await self.session.flush()
        return document

    async def get_document_by_id(self, document_id: UUID) -> DocumentMetadata | None:
        statement = select(DocumentMetadata).where(DocumentMetadata.id == document_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_documents_for_profile(self, profile_id: UUID) -> Sequence[DocumentMetadata]:
        statement = select(DocumentMetadata).where(DocumentMetadata.profile_id == profile_id, DocumentMetadata.deleted_at.is_(None)).order_by(DocumentMetadata.created_at.desc())
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def delete_document(self, document_id: UUID, deleted_at: datetime) -> DocumentMetadata | None:
        document = await self.get_document_by_id(document_id)
        if document is None:
            return None
        document.deleted_at = deleted_at
        await self.session.flush()
        return document


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(self, event: AuditEvent) -> AuditEvent:
        event_model = AuditEventModel(
            event_type=event.event_type,
            actor_subject=event.actor_subject,
            aggregate_id=event.aggregate_id,
            action=event.action,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            outcome=event.outcome,
            payload=event.payload,
            details=event.details,
        )
        self.session.add(event_model)
        await self.session.flush()
        return event