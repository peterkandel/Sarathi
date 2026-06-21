from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import get_application_service
from app.application.services import ApplicationService
from app.domain.schemas import ApplicationCreate, ApplicationDocumentCreate, ApplicationDocumentRead, ApplicationHistoryRead, ApplicationRead, ApplicationStatusRead, MessageResponse
from shared_auth import get_principal


router = APIRouter(tags=["application"])


@router.post("/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(request: Request, payload: ApplicationCreate, service: ApplicationService = Depends(get_application_service)) -> ApplicationRead:
    application = await service.create_application(payload, get_principal(request))
    return ApplicationRead.model_validate(application, from_attributes=True)


@router.post("/applications/{application_id}/documents", response_model=ApplicationDocumentRead, status_code=status.HTTP_201_CREATED)
async def attach_document(application_id: UUID, request: Request, payload: ApplicationDocumentCreate, service: ApplicationService = Depends(get_application_service)) -> ApplicationDocumentRead:
    document = await service.attach_document(application_id, payload, get_principal(request))
    return ApplicationDocumentRead.model_validate(document, from_attributes=True)


@router.post("/applications/{application_id}/submit", response_model=ApplicationRead)
async def submit_application(application_id: UUID, request: Request, service: ApplicationService = Depends(get_application_service)) -> ApplicationRead:
    application = await service.submit_application(application_id, get_principal(request))
    return ApplicationRead.model_validate(application, from_attributes=True)


@router.get("/applications/{application_id}/status", response_model=ApplicationStatusRead)
async def get_status(application_id: UUID, request: Request, service: ApplicationService = Depends(get_application_service)) -> ApplicationStatusRead:
    return await service.get_status(application_id, get_principal(request))


@router.get("/applications/{application_id}/history", response_model=list[ApplicationHistoryRead])
async def get_history(application_id: UUID, request: Request, service: ApplicationService = Depends(get_application_service)) -> list[ApplicationHistoryRead]:
    events = await service.get_history(application_id, get_principal(request))
    return [ApplicationHistoryRead.model_validate(event, from_attributes=True) for event in events]


@router.get("/applications/{application_id}", response_model=ApplicationRead)
async def get_application(application_id: UUID, request: Request, service: ApplicationService = Depends(get_application_service)) -> ApplicationRead:
    application = await service.get_application(application_id, get_principal(request))
    return ApplicationRead.model_validate(application, from_attributes=True)


@router.delete("/applications/{application_id}", response_model=MessageResponse)
async def delete_application(application_id: UUID, request: Request, service: ApplicationService = Depends(get_application_service)) -> MessageResponse:
    _ = application_id
    _ = get_principal(request)
    return MessageResponse(message="Application deletion is not implemented")
