from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import CitizenService
from app.infrastructure.db import get_session
from app.infrastructure.repositories import AuditRepository, CitizenProfileRepository, CitizenshipRecordRepository, DocumentMetadataRepository


async def get_profile_repository(session: AsyncSession = Depends(get_session)) -> CitizenProfileRepository:
    return CitizenProfileRepository(session)


async def get_record_repository(session: AsyncSession = Depends(get_session)) -> CitizenshipRecordRepository:
    return CitizenshipRecordRepository(session)


async def get_document_repository(session: AsyncSession = Depends(get_session)) -> DocumentMetadataRepository:
    return DocumentMetadataRepository(session)


async def get_audit_repository(session: AsyncSession = Depends(get_session)) -> AuditRepository:
    return AuditRepository(session)


async def get_citizen_service(
    profile_repository: CitizenProfileRepository = Depends(get_profile_repository),
    record_repository: CitizenshipRecordRepository = Depends(get_record_repository),
    document_repository: DocumentMetadataRepository = Depends(get_document_repository),
    audit_repository: AuditRepository = Depends(get_audit_repository),
) -> CitizenService:
    return CitizenService(profile_repository, record_repository, document_repository, audit_repository)