from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import OcrService
from app.infrastructure.db import get_session
from app.infrastructure.providers import get_default_ocr_provider
from app.infrastructure.repositories import AuditRepository, OcrArtifactRepository, OcrEventRepository, OcrJobRepository
from app.infrastructure.storage import FileSystemObjectStorage


async def get_ocr_job_repository(session: AsyncSession = Depends(get_session)) -> OcrJobRepository:
    return OcrJobRepository(session)


async def get_ocr_artifact_repository(session: AsyncSession = Depends(get_session)) -> OcrArtifactRepository:
    return OcrArtifactRepository(session)


async def get_ocr_event_repository(session: AsyncSession = Depends(get_session)) -> OcrEventRepository:
    return OcrEventRepository(session)


async def get_audit_repository(session: AsyncSession = Depends(get_session)) -> AuditRepository:
    return AuditRepository(session)


async def get_storage_service() -> FileSystemObjectStorage:
    return FileSystemObjectStorage()


async def get_ocr_provider():
    return get_default_ocr_provider()


async def get_ocr_service(
    job_repository: OcrJobRepository = Depends(get_ocr_job_repository),
    artifact_repository: OcrArtifactRepository = Depends(get_ocr_artifact_repository),
    event_repository: OcrEventRepository = Depends(get_ocr_event_repository),
    audit_repository: AuditRepository = Depends(get_audit_repository),
    storage_service: FileSystemObjectStorage = Depends(get_storage_service),
    ocr_engine = Depends(get_ocr_provider),
) -> OcrService:
    return OcrService(job_repository, artifact_repository, event_repository, audit_repository, storage_service, ocr_engine)
