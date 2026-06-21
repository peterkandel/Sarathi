from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import AuditEvent, ApplicationHistoryEventCreate
from app.domain.models import Application, ApplicationDocument, ApplicationHistoryEvent
from app.domain.models import Application as ApplicationModel
from app.domain.models import ApplicationDocument as ApplicationDocumentModel
from app.domain.models import ApplicationHistoryEvent as ApplicationHistoryEventModel


class ApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_application(self, application: Application) -> Application:
        self.session.add(application)
        await self.session.flush()
        return application

    async def update_application(self, application: Application) -> Application:
        self.session.add(application)
        await self.session.flush()
        return application

    async def get_application_by_id(self, application_id: UUID) -> Application | None:
        result = await self.session.execute(select(ApplicationModel).where(ApplicationModel.id == application_id))
        return result.scalar_one_or_none()

    async def get_application_by_reference(self, reference_number: str) -> Application | None:
        result = await self.session.execute(select(ApplicationModel).where(ApplicationModel.reference_number == reference_number))
        return result.scalar_one_or_none()

    async def list_applications_for_subject(self, applicant_subject: str) -> Sequence[Application]:
        result = await self.session.execute(select(ApplicationModel).where(ApplicationModel.applicant_subject == applicant_subject, ApplicationModel.deleted_at.is_(None)).order_by(ApplicationModel.created_at.desc()))
        return list(result.scalars().all())


class ApplicationDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_document(self, document: ApplicationDocument) -> ApplicationDocument:
        self.session.add(document)
        await self.session.flush()
        return document

    async def get_document_by_id(self, document_id: UUID) -> ApplicationDocument | None:
        result = await self.session.execute(select(ApplicationDocumentModel).where(ApplicationDocumentModel.id == document_id))
        return result.scalar_one_or_none()

    async def list_documents_for_application(self, application_id: UUID) -> Sequence[ApplicationDocument]:
        result = await self.session.execute(select(ApplicationDocumentModel).where(ApplicationDocumentModel.application_id == application_id, ApplicationDocumentModel.deleted_at.is_(None)).order_by(ApplicationDocumentModel.created_at.desc()))
        return list(result.scalars().all())


class ApplicationHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_event(self, event: ApplicationHistoryEventCreate, application_id: UUID) -> ApplicationHistoryEvent:
        event_model = ApplicationHistoryEventModel(
            application_id=application_id,
            event_type=event.event_type,
            notes=event.notes,
            payload=event.payload,
            recorded_by_subject=event.recorded_by_subject,
            recorded_at=event.recorded_at or datetime.now(timezone.utc),
        )
        self.session.add(event_model)
        await self.session.flush()
        return event_model

    async def list_events_for_application(self, application_id: UUID) -> Sequence[ApplicationHistoryEvent]:
        result = await self.session.execute(select(ApplicationHistoryEventModel).where(ApplicationHistoryEventModel.application_id == application_id).order_by(ApplicationHistoryEventModel.recorded_at.asc()))
        return list(result.scalars().all())


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(self, event: AuditEvent) -> AuditEvent:
        _ = event
        return event
