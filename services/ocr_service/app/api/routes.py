from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status

from app.api.dependencies import get_ocr_service
from app.application.services import OcrService
from app.domain.schemas import OcrJobConfidenceRead, OcrJobCreateResponse, OcrJobPriority, OcrJobRead, OcrReprocessRequest
from app.domain.schemas import OcrErrorResponse
from shared_auth import Permission, get_principal
from shared_auth.security import has_permission


router = APIRouter(tags=["ocr"])


@router.post("/jobs", response_model=OcrJobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    request: Request,
    document_id: UUID = Form(...),
    file_id: UUID = Form(...),
    document_type_code: str = Form(...),
    priority: OcrJobPriority = Form(default=OcrJobPriority.NORMAL),
    file: UploadFile = File(...),
    service: OcrService = Depends(get_ocr_service),
) -> OcrJobRead:
    job = await service.create_job(document_id=document_id, file_id=file_id, document_type_code=document_type_code, priority=priority, upload_file=file, principal=get_principal(request))
    return OcrJobRead.model_validate(job, from_attributes=True)


@router.get("/jobs/{job_id}", response_model=OcrJobRead)
async def get_job(job_id: UUID, request: Request, service: OcrService = Depends(get_ocr_service)) -> OcrJobRead:
    job = await service.get_job(job_id, get_principal(request))
    return OcrJobRead.model_validate(job, from_attributes=True)


@router.post("/jobs/{job_id}/reprocess", response_model=OcrJobRead)
async def reprocess_job(job_id: UUID, request: Request, payload: OcrReprocessRequest, service: OcrService = Depends(get_ocr_service)) -> OcrJobRead:
    job = await service.reprocess_job(job_id, payload, get_principal(request))
    return OcrJobRead.model_validate(job, from_attributes=True)


@router.get("/jobs/{job_id}/confidence", response_model=OcrJobConfidenceRead)
async def get_confidence(job_id: UUID, request: Request, service: OcrService = Depends(get_ocr_service)) -> OcrJobConfidenceRead:
    return await service.get_job_confidence(job_id, get_principal(request))


@router.get("/jobs/{job_id}/events")
async def get_events(job_id: UUID, request: Request, service: OcrService = Depends(get_ocr_service)):
    return await service.list_job_events(job_id, get_principal(request))
