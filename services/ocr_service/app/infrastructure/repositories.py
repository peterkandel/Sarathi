from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import AuditEvent, OcrJobEventPayload
from app.domain.models import OcrJob, OcrJobArtifact, OcrJobEvent


class OcrJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_job(self, job: OcrJob) -> OcrJob:
        self.session.add(job)
        await self.session.flush()
        return job

    async def update_job(self, job: OcrJob) -> OcrJob:
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_job_by_id(self, job_id: UUID) -> OcrJob | None:
        result = await self.session.execute(select(OcrJob).where(OcrJob.id == job_id))
        return result.scalar_one_or_none()


class OcrArtifactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_artifact(self, artifact: OcrJobArtifact) -> OcrJobArtifact:
        self.session.add(artifact)
        await self.session.flush()
        return artifact

    async def list_artifacts_for_job(self, job_id: UUID) -> Sequence[OcrJobArtifact]:
        result = await self.session.execute(select(OcrJobArtifact).where(OcrJobArtifact.job_id == job_id).order_by(OcrJobArtifact.created_at.asc()))
        return list(result.scalars().all())


class OcrEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_event(self, job_id: UUID, event: OcrJobEventPayload) -> OcrJobEvent:
        event_model = OcrJobEvent(
            job_id=job_id,
            event_type=event.event_type,
            stage=event.stage,
            message=event.message,
            payload=event.payload,
            recorded_at=event.recorded_at or datetime.now(timezone.utc),
        )
        self.session.add(event_model)
        await self.session.flush()
        return event_model

    async def list_events_for_job(self, job_id: UUID) -> Sequence[OcrJobEvent]:
        result = await self.session.execute(select(OcrJobEvent).where(OcrJobEvent.job_id == job_id).order_by(OcrJobEvent.recorded_at.asc()))
        return list(result.scalars().all())


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(self, event: AuditEvent) -> AuditEvent:
        _ = event
        return event
