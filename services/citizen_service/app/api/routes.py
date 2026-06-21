from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import get_citizen_service
from app.application.services import CitizenService
from app.domain.schemas import (
    CitizenProfileCreate,
    CitizenProfileRead,
    CitizenProfileUpdate,
    CitizenshipRecordCreate,
    CitizenshipRecordRead,
    CitizenshipRecordUpdate,
    DocumentMetadataCreate,
    DocumentMetadataRead,
    DocumentMetadataUpdate,
    MessageResponse,
)
from shared_auth import get_principal


router = APIRouter(tags=["citizen"])


@router.post("/profiles", response_model=CitizenProfileRead, status_code=status.HTTP_201_CREATED)
async def create_profile(request: Request, payload: CitizenProfileCreate, service: CitizenService = Depends(get_citizen_service)) -> CitizenProfileRead:
    profile = await service.create_profile(payload, get_principal(request))
    return CitizenProfileRead.model_validate(profile, from_attributes=True)


@router.get("/profiles/me", response_model=CitizenProfileRead)
async def get_my_profile(request: Request, service: CitizenService = Depends(get_citizen_service)) -> CitizenProfileRead:
    profile = await service.get_profile_by_identity_subject(get_principal(request).subject, get_principal(request))
    return CitizenProfileRead.model_validate(profile, from_attributes=True)


@router.get("/profiles", response_model=list[CitizenProfileRead])
async def list_profiles(request: Request, service: CitizenService = Depends(get_citizen_service)) -> list[CitizenProfileRead]:
    profiles = await service.list_profiles(get_principal(request))
    return [CitizenProfileRead.model_validate(profile, from_attributes=True) for profile in profiles]


@router.get("/profiles/{profile_id}", response_model=CitizenProfileRead)
async def get_profile(profile_id: UUID, request: Request, service: CitizenService = Depends(get_citizen_service)) -> CitizenProfileRead:
    profile = await service.get_profile_by_id(profile_id, get_principal(request))
    return CitizenProfileRead.model_validate(profile, from_attributes=True)


@router.patch("/profiles/{profile_id}", response_model=CitizenProfileRead)
async def update_profile(profile_id: UUID, request: Request, payload: CitizenProfileUpdate, service: CitizenService = Depends(get_citizen_service)) -> CitizenProfileRead:
    profile = await service.update_profile(profile_id, payload, get_principal(request))
    return CitizenProfileRead.model_validate(profile, from_attributes=True)


@router.delete("/profiles/{profile_id}", response_model=MessageResponse)
async def delete_profile(profile_id: UUID, request: Request, service: CitizenService = Depends(get_citizen_service)) -> MessageResponse:
    await service.delete_profile(profile_id, get_principal(request))
    return MessageResponse(message="Profile deleted")


@router.post("/profiles/{profile_id}/citizenship-records", response_model=CitizenshipRecordRead, status_code=status.HTTP_201_CREATED)
async def create_citizenship_record(profile_id: UUID, request: Request, payload: CitizenshipRecordCreate, service: CitizenService = Depends(get_citizen_service)) -> CitizenshipRecordRead:
    record = await service.create_record(profile_id, payload, get_principal(request))
    return CitizenshipRecordRead.model_validate(record, from_attributes=True)


@router.get("/profiles/{profile_id}/citizenship-records", response_model=list[CitizenshipRecordRead])
async def list_citizenship_records(profile_id: UUID, request: Request, service: CitizenService = Depends(get_citizen_service)) -> list[CitizenshipRecordRead]:
    records = await service.list_records(profile_id, get_principal(request))
    return [CitizenshipRecordRead.model_validate(record, from_attributes=True) for record in records]


@router.get("/citizenship-records/{record_id}", response_model=CitizenshipRecordRead)
async def get_citizenship_record(record_id: UUID, request: Request, service: CitizenService = Depends(get_citizen_service)) -> CitizenshipRecordRead:
    record = await service.get_record(record_id, get_principal(request))
    return CitizenshipRecordRead.model_validate(record, from_attributes=True)


@router.patch("/citizenship-records/{record_id}", response_model=CitizenshipRecordRead)
async def update_citizenship_record(record_id: UUID, request: Request, payload: CitizenshipRecordUpdate, service: CitizenService = Depends(get_citizen_service)) -> CitizenshipRecordRead:
    record = await service.update_record(record_id, payload, get_principal(request))
    return CitizenshipRecordRead.model_validate(record, from_attributes=True)


@router.delete("/citizenship-records/{record_id}", response_model=MessageResponse)
async def delete_citizenship_record(record_id: UUID, request: Request, service: CitizenService = Depends(get_citizen_service)) -> MessageResponse:
    await service.delete_record(record_id, get_principal(request))
    return MessageResponse(message="Citizenship record deleted")


@router.post("/profiles/{profile_id}/documents", response_model=DocumentMetadataRead, status_code=status.HTTP_201_CREATED)
async def create_document(profile_id: UUID, request: Request, payload: DocumentMetadataCreate, service: CitizenService = Depends(get_citizen_service)) -> DocumentMetadataRead:
    document = await service.create_document(profile_id, payload, get_principal(request))
    return DocumentMetadataRead.model_validate(document, from_attributes=True)


@router.get("/profiles/{profile_id}/documents", response_model=list[DocumentMetadataRead])
async def list_documents(profile_id: UUID, request: Request, service: CitizenService = Depends(get_citizen_service)) -> list[DocumentMetadataRead]:
    documents = await service.list_documents(profile_id, get_principal(request))
    return [DocumentMetadataRead.model_validate(document, from_attributes=True) for document in documents]


@router.get("/documents/{document_id}", response_model=DocumentMetadataRead)
async def get_document(document_id: UUID, request: Request, service: CitizenService = Depends(get_citizen_service)) -> DocumentMetadataRead:
    document = await service.get_document(document_id, get_principal(request))
    return DocumentMetadataRead.model_validate(document, from_attributes=True)


@router.patch("/documents/{document_id}", response_model=DocumentMetadataRead)
async def update_document(document_id: UUID, request: Request, payload: DocumentMetadataUpdate, service: CitizenService = Depends(get_citizen_service)) -> DocumentMetadataRead:
    document = await service.update_document(document_id, payload, get_principal(request))
    return DocumentMetadataRead.model_validate(document, from_attributes=True)


@router.delete("/documents/{document_id}", response_model=MessageResponse)
async def delete_document(document_id: UUID, request: Request, service: CitizenService = Depends(get_citizen_service)) -> MessageResponse:
    await service.delete_document(document_id, get_principal(request))
    return MessageResponse(message="Document deleted")