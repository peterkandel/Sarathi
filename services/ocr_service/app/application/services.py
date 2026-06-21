from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.domain.events import AuditEvent, OcrJobEventPayload, OcrErrorPayload
from app.domain.models import OcrArtifactStage, OcrJob, OcrJobStatus, OcrRiskLevel
from app.domain.ports import ObjectStorageProtocol, OcrProviderProtocol
from app.domain.schemas import OcrJobConfidenceRead, OcrJobPriority, OcrReprocessRequest
from app.infrastructure.repositories import AuditRepository, OcrArtifactRepository, OcrEventRepository, OcrJobRepository
from shared_auth import Permission
from shared_auth.models import Principal
from shared_auth.security import has_permission


class OcrServiceError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(status_code=status_code, detail={"error_code": code, "message": message, "details": details or {}})
        self.code = code
        self.message = message
        self.details = details or {}


class OcrService:
    def __init__(
        self,
        jobs: OcrJobRepository,
        artifacts: OcrArtifactRepository,
        events: OcrEventRepository,
        audit: AuditRepository,
        storage: ObjectStorageProtocol,
        provider: OcrProviderProtocol,
    ) -> None:
        self.jobs = jobs
        self.artifacts = artifacts
        self.events = events
        self.audit = audit
        self.storage = storage
        self.provider = provider

    def _can_review(self, principal: Principal) -> bool:
        return has_permission(principal, Permission.VERIFY_OCR)

    def _validate_upload(self, upload_file: UploadFile, content: bytes) -> None:
        if upload_file.content_type not in settings.supported_mime_type_list:
            raise OcrServiceError(status.HTTP_400_BAD_REQUEST, "OCR-4001", "Unsupported file format", {"mime_type": upload_file.content_type})
        if len(content) > settings.max_upload_size_bytes:
            raise OcrServiceError(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "OCR-4002", "File exceeds allowed upload size", {"max_upload_size_bytes": settings.max_upload_size_bytes})
        if len(content) < 16:
            raise OcrServiceError(status.HTTP_400_BAD_REQUEST, "OCR-4003", "Image quality is too low", {"reason": "empty_or_truncated_upload"})

    async def create_job(
        self,
        *,
        document_id: UUID,
        file_id: UUID,
        document_type_code: str,
        priority: OcrJobPriority,
        upload_file: UploadFile,
        principal: Principal,
    ) -> OcrJob:
        content = await upload_file.read()
        self._validate_upload(upload_file, content)

        checksum_sha256 = hashlib.sha256(content).hexdigest()
        original_storage_key = f"ocr/{document_id}/{file_id}/original-{upload_file.filename}"
        await self.storage.save(original_storage_key, content, upload_file.content_type or "application/octet-stream")

        job = OcrJob(
            document_id=document_id,
            file_id=file_id,
            document_type_code=document_type_code,
            priority=priority.value,
            status=OcrJobStatus.QUEUED.value,
            file_name=upload_file.filename or "citizenship-image",
            mime_type=upload_file.content_type or "application/octet-stream",
            original_storage_key=original_storage_key,
            model_name=settings.ocr_engine_name,
            model_version=settings.ocr_model_version,
            pipeline_version="1.0",
            created_by_subject=principal.subject,
            updated_by_subject=principal.subject,
        )
        job = await self.jobs.create_job(job)
        await self.events.create_event(job.id, OcrJobEventPayload(event_type="JobQueued", stage="upload", message="OCR job queued", payload={"document_id": str(document_id), "file_id": str(file_id), "checksum_sha256": checksum_sha256}))
        await self.audit.record_event(AuditEvent(event_type="OcrJobQueued", actor_subject=principal.subject, aggregate_id=job.id, action="create_job", resource_type="ocr_job", resource_id=str(job.id), outcome="success", payload={"document_type_code": document_type_code}))
        return await self._process_job(job.id, content, principal, original_storage_key=original_storage_key)

    async def get_job(self, job_id: UUID, principal: Principal) -> OcrJob:
        job = await self.jobs.get_job_by_id(job_id)
        if job is None or job.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR job not found")
        if job.created_by_subject != principal.subject and not self._can_review(principal):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="OCR job access denied")
        return job

    async def get_job_confidence(self, job_id: UUID, principal: Principal) -> OcrJobConfidenceRead:
        job = await self.get_job(job_id, principal)
        return self._confidence_response(job)

    async def reprocess_job(self, job_id: UUID, payload: OcrReprocessRequest, principal: Principal) -> OcrJob:
        if not self._can_review(principal):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="OCR reprocessing requires review permission")
        job = await self.get_job(job_id, principal)
        if job.status == OcrJobStatus.RUNNING.value:
            raise OcrServiceError(status.HTTP_409_CONFLICT, "OCR-5031", "Job is currently running", {"job_id": str(job.id)})
        original_bytes = await self.storage.load(job.original_storage_key)
        if payload.model_version:
            job.model_version = payload.model_version
        if payload.force_human_review:
            job.status = OcrJobStatus.REVIEW_REQUIRED.value
            job.validation_status = "REVIEW_REQUIRED"
            job.structured_output = {**job.structured_output, "review_required": True}
            job.updated_by_subject = principal.subject
            job = await self.jobs.update_job(job)
            await self.events.create_event(job.id, OcrJobEventPayload(event_type="JobMarkedForReview", stage="validation", message="Manual review requested", payload={"force_human_review": True}))
            return job
        return await self._process_job(job.id, original_bytes, principal, original_storage_key=job.original_storage_key)

    async def _process_job(self, job_id: UUID, content: bytes, principal: Principal, *, original_storage_key: str) -> OcrJob:
        job = await self.jobs.get_job_by_id(job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR job not found")
        job.status = OcrJobStatus.RUNNING.value
        job.updated_by_subject = principal.subject
        job = await self.jobs.update_job(job)

        from app.domain.ports import UploadedDocument

        uploaded_document = UploadedDocument(file_name=job.file_name, mime_type=job.mime_type, content=content, checksum_sha256=hashlib.sha256(content).hexdigest(), size_bytes=len(content))
        await self.events.create_event(job.id, OcrJobEventPayload(event_type="PreprocessingStarted", stage="preprocessing", message="Preprocessing started"))
        preprocessed = await self.provider.preprocess(uploaded_document)
        normalized_storage_key = original_storage_key.replace("original-", "normalized-")
        await self.storage.save(normalized_storage_key, preprocessed.normalized_bytes, job.mime_type)
        normalized_artifact = await self.artifacts.create_artifact(
            __import__("app.domain.models", fromlist=["OcrJobArtifact"]).OcrJobArtifact(
                job_id=job.id,
                stage=OcrArtifactStage.PREPROCESSING.value,
                artifact_type="normalized_image",
                storage_key=normalized_storage_key,
                mime_type=job.mime_type,
                checksum_sha256=hashlib.sha256(preprocessed.normalized_bytes).hexdigest(),
                size_bytes=len(preprocessed.normalized_bytes),
                artifact_metadata={"quality_score": preprocessed.quality_score, "page_count": preprocessed.page_count},
            )
        )
        _ = normalized_artifact
        await self.events.create_event(job.id, OcrJobEventPayload(event_type="OcrInferenceStarted", stage="ocr", message="OCR inference started"))
        text_result = await self.provider.recognize_text(preprocessed, job.document_type_code)
        field_results = list(await self.provider.extract_fields(text_result, job.document_type_code))
        validation_result = await self.provider.validate(field_results, job.document_type_code)

        field_confidences = [
            {"field_name": field.field_name, "confidence": field.confidence, "validation_status": field.validation_status, "source_language": field.source_language, "normalized_value": field.normalized_value}
            for field in field_results
        ]
        field_confidence = self._average([field.confidence for field in field_results])
        preprocessing_confidence = preprocessed.quality_score
        ocr_confidence = text_result.confidence
        validation_confidence = 1.0 if validation_result.status == "PASS" else max(0.3, 1.0 - (0.2 * len(validation_result.issues)))
        document_confidence = self._round(0.2 * preprocessing_confidence + 0.35 * ocr_confidence + 0.25 * field_confidence + 0.2 * validation_confidence)
        risk_score = self._round(min(1.0, (1.0 - preprocessing_confidence) * 0.35 + (1.0 - document_confidence) * 0.45 + (0.1 * len(validation_result.issues))))
        risk_level = self._risk_level(risk_score)
        validation_status = "PASS" if validation_result.status == "PASS" and risk_level == OcrRiskLevel.LOW.value else "REVIEW_REQUIRED" if risk_level != OcrRiskLevel.LOW.value else "PASS"
        if validation_status == "REVIEW_REQUIRED":
            job.status = OcrJobStatus.REVIEW_REQUIRED.value
        else:
            job.status = OcrJobStatus.COMPLETED.value
        job.normalized_storage_key = normalized_storage_key
        job.document_confidence = document_confidence
        job.risk_score = risk_score
        job.validation_status = validation_status
        job.structured_output = {
            "text": text_result.text,
            "page_count": preprocessed.page_count,
            "fields": [field.__dict__ for field in field_results],
            "validation_status": validation_status,
            "validation_issues": [issue.__dict__ for issue in validation_result.issues],
            "document_confidence": document_confidence,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "model_name": job.model_name,
            "model_version": job.model_version,
            "preprocessing": {"quality_score": preprocessing_confidence, "page_count": preprocessed.page_count},
            "raw_ocr": {"text_confidence": ocr_confidence, "metadata": text_result.metadata},
        }
        job.completed_at = datetime.now(timezone.utc)
        job.updated_by_subject = principal.subject
        job = await self.jobs.update_job(job)
        await self.events.create_event(job.id, OcrJobEventPayload(event_type="JobCompleted" if job.status == OcrJobStatus.COMPLETED.value else "JobFlaggedForReview", stage="validation", message="OCR processing complete", payload={"document_confidence": document_confidence, "risk_score": risk_score, "risk_level": risk_level}))
        await self.audit.record_event(AuditEvent(event_type="OcrJobProcessed", actor_subject=principal.subject, aggregate_id=job.id, action="process_job", resource_type="ocr_job", resource_id=str(job.id), outcome="success", payload={"status": job.status, "risk_level": risk_level}))
        return job

    async def list_job_events(self, job_id: UUID, principal: Principal) -> list[dict[str, object]]:
        job = await self.get_job(job_id, principal)
        events = await self.events.list_events_for_job(job.id)
        return [
            {
                "id": event.id,
                "job_id": event.job_id,
                "event_type": event.event_type,
                "stage": event.stage,
                "message": event.message,
                "payload": event.payload,
                "recorded_at": event.recorded_at,
            }
            for event in events
        ]

    def _confidence_response(self, job: OcrJob) -> OcrJobConfidenceRead:
        structured = job.structured_output or {}
        field_confidences = structured.get("fields", [])
        preprocessing_confidence = float((structured.get("preprocessing") or {}).get("quality_score", job.document_confidence or 0.0))
        ocr_confidence = float((structured.get("raw_ocr") or {}).get("text_confidence", job.document_confidence or 0.0))
        validation_confidence = 1.0 if job.validation_status == "PASS" else 0.6
        risk_score = float(job.risk_score or 0.0)
        return OcrJobConfidenceRead(
            job_id=job.id,
            document_confidence=float(job.document_confidence or 0.0),
            preprocessing_confidence=preprocessing_confidence,
            ocr_confidence=ocr_confidence,
            validation_confidence=validation_confidence,
            risk_score=risk_score,
            risk_level=self._risk_level(risk_score),
            model_name=job.model_name,
            model_version=job.model_version,
            field_confidences=field_confidences,
        )

    def _risk_level(self, risk_score: float) -> str:
        if risk_score >= 0.7:
            return OcrRiskLevel.HIGH.value
        if risk_score >= 0.4:
            return OcrRiskLevel.MEDIUM.value
        return OcrRiskLevel.LOW.value

    def _average(self, values: list[float]) -> float:
        return self._round(sum(values) / len(values)) if values else 0.0

    def _round(self, value: float) -> float:
        return round(value, 4)
