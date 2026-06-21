from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import ApplicationService
from app.infrastructure.db import get_session
from app.infrastructure.repositories import ApplicationDocumentRepository, ApplicationHistoryRepository, ApplicationRepository, AuditRepository
from app.infrastructure.workflow_client import WorkflowServiceClient


async def get_application_repository(session: AsyncSession = Depends(get_session)) -> ApplicationRepository:
    return ApplicationRepository(session)


async def get_application_document_repository(session: AsyncSession = Depends(get_session)) -> ApplicationDocumentRepository:
    return ApplicationDocumentRepository(session)


async def get_application_history_repository(session: AsyncSession = Depends(get_session)) -> ApplicationHistoryRepository:
    return ApplicationHistoryRepository(session)


async def get_audit_repository(session: AsyncSession = Depends(get_session)) -> AuditRepository:
    return AuditRepository(session)


async def get_workflow_client() -> WorkflowServiceClient:
    return WorkflowServiceClient()


async def get_application_service(
    application_repository: ApplicationRepository = Depends(get_application_repository),
    document_repository: ApplicationDocumentRepository = Depends(get_application_document_repository),
    history_repository: ApplicationHistoryRepository = Depends(get_application_history_repository),
    audit_repository: AuditRepository = Depends(get_audit_repository),
    workflow_client: WorkflowServiceClient = Depends(get_workflow_client),
) -> ApplicationService:
    return ApplicationService(application_repository, document_repository, history_repository, audit_repository, workflow_client)
