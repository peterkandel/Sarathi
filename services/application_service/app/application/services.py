from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.domain.events import AuditEvent, ApplicationHistoryEventCreate
from app.domain.models import Application, ApplicationDocument, ApplicationStatus
from app.domain.models import ApplicationHistoryEvent
from app.domain.ports import ApplicationDocumentRepositoryProtocol, ApplicationHistoryRepositoryProtocol, ApplicationRepositoryProtocol, AuditRepositoryProtocol, WorkflowClientProtocol
from app.domain.schemas import ApplicationCreate, ApplicationDocumentCreate, ApplicationRead, ApplicationStatusRead
from shared_auth import Role
from shared_auth.models import Principal
from shared_auth.security import has_any_role


ADMIN_ROLES = (Role.ADMINISTRATOR, Role.SUPER_ADMINISTRATOR)


class ApplicationService:
    def __init__(
        self,
        applications: ApplicationRepositoryProtocol,
        documents: ApplicationDocumentRepositoryProtocol,
        history: ApplicationHistoryRepositoryProtocol,
        audit: AuditRepositoryProtocol,
        workflow_client: WorkflowClientProtocol,
    ) -> None:
        self.applications = applications
        self.documents = documents
        self.history = history
        self.audit = audit
        self.workflow_client = workflow_client

    def _is_admin(self, principal: Principal) -> bool:
        return has_any_role(principal, ADMIN_ROLES)

    async def _get_application(self, application_id: UUID, principal: Principal) -> Application:
        application = await self.applications.get_application_by_id(application_id)
        if application is None or application.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        if application.applicant_subject != principal.subject and not self._is_admin(principal):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Application access denied")
        return application

    async def create_application(self, payload: ApplicationCreate, principal: Principal) -> Application:
        reference_number = f"APP-{uuid4().hex[:12].upper()}"
        application = Application(
            reference_number=reference_number,
            applicant_subject=principal.subject,
            workflow_definition_code=payload.workflow_definition_code,
            workflow_definition_version=payload.workflow_definition_version,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            title=payload.title,
            description=payload.description,
            application_status=ApplicationStatus.DRAFT.value,
            payload=payload.payload,
            application_metadata=payload.application_metadata,
            created_by_subject=principal.subject,
            updated_by_subject=principal.subject,
        )
        created = await self.applications.create_application(application)
        await self.history.create_event(ApplicationHistoryEventCreate(event_type="ApplicationCreated", notes="Application draft created", payload={"reference_number": reference_number}, recorded_by_subject=principal.subject), created.id)
        await self.audit.record_event(AuditEvent(event_type="ApplicationCreated", actor_subject=principal.subject, aggregate_id=created.id, action="create_application", resource_type="application", resource_id=str(created.id), outcome="success", payload={"reference_number": reference_number}))
        return created

    async def attach_document(self, application_id: UUID, payload: ApplicationDocumentCreate, principal: Principal) -> ApplicationDocument:
        application = await self._get_application(application_id, principal)
        if application.application_status != ApplicationStatus.DRAFT.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Documents can only be attached while the application is a draft")
        document = ApplicationDocument(
            application_id=application.id,
            document_type=payload.document_type,
            file_name=payload.file_name,
            mime_type=payload.mime_type,
            storage_key=payload.storage_key,
            checksum_sha256=payload.checksum_sha256.lower(),
            size_bytes=payload.size_bytes,
            document_metadata=payload.document_metadata,
            created_by_subject=principal.subject,
            updated_by_subject=principal.subject,
        )
        created = await self.documents.create_document(document)
        await self.history.create_event(ApplicationHistoryEventCreate(event_type="DocumentAttached", notes=payload.file_name, payload={"storage_key": payload.storage_key, "document_type": payload.document_type}, recorded_by_subject=principal.subject), application.id)
        await self.audit.record_event(AuditEvent(event_type="ApplicationDocumentAttached", actor_subject=principal.subject, aggregate_id=application.id, action="attach_document", resource_type="application_document", resource_id=str(created.id), outcome="success", payload={"storage_key": payload.storage_key}))
        return created

    async def submit_application(self, application_id: UUID, principal: Principal) -> Application:
        application = await self._get_application(application_id, principal)
        if application.application_status != ApplicationStatus.DRAFT.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application has already been submitted")
        documents = await self.documents.list_documents_for_application(application.id)
        if not documents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one document is required before submission")
        workflow_application = await self.workflow_client.submit_application(
            definition_code=application.workflow_definition_code,
            definition_version=application.workflow_definition_version,
            entity_type=application.entity_type,
            entity_id=application.entity_id,
            title=application.title,
            payload=application.payload,
            application_metadata=application.application_metadata,
            applicant_subject=principal.subject,
        )
        application.application_status = ApplicationStatus.SUBMITTED.value
        application.workflow_application_id = UUID(str(workflow_application["id"]))
        application.workflow_status = str(workflow_application.get("status") or "SUBMITTED")
        application.workflow_current_state_id = UUID(str(workflow_application["current_state_id"]))
        application.workflow_current_state_code = workflow_application.get("workflow_current_state_code") or workflow_application.get("current_state_code")
        application.submitted_at = datetime.now(timezone.utc)
        application.updated_by_subject = principal.subject
        updated = await self.applications.update_application(application)
        await self.history.create_event(ApplicationHistoryEventCreate(event_type="ApplicationSubmitted", notes="Application submitted to workflow", payload={"workflow_application_id": str(updated.workflow_application_id)}, recorded_by_subject=principal.subject), updated.id)
        await self.audit.record_event(AuditEvent(event_type="ApplicationSubmitted", actor_subject=principal.subject, aggregate_id=updated.id, action="submit_application", resource_type="application", resource_id=str(updated.id), outcome="success", payload={"workflow_application_id": str(updated.workflow_application_id)}))
        return updated

    async def get_status(self, application_id: UUID, principal: Principal) -> ApplicationStatusRead:
        application = await self._get_application(application_id, principal)
        if application.workflow_application_id is not None:
            workflow_application = await self.workflow_client.get_application(str(application.workflow_application_id))
            application.workflow_status = str(workflow_application.get("status") or application.workflow_status)
            current_state_id = workflow_application.get("current_state_id")
            if current_state_id is not None:
                application.workflow_current_state_id = UUID(str(current_state_id))
            application.updated_by_subject = principal.subject
            application = await self.applications.update_application(application)
            await self.history.create_event(ApplicationHistoryEventCreate(event_type="WorkflowStatusSynced", notes="Workflow status refreshed", payload={"workflow_status": application.workflow_status}, recorded_by_subject=principal.subject), application.id)
        document_count = len(await self.documents.list_documents_for_application(application.id))
        return ApplicationStatusRead(
            application_id=application.id,
            application_status=application.application_status,
            workflow_application_id=application.workflow_application_id,
            workflow_status=application.workflow_status,
            workflow_current_state_id=application.workflow_current_state_id,
            workflow_current_state_code=application.workflow_current_state_code,
            submitted_at=application.submitted_at,
            resolved_at=application.resolved_at,
            document_count=document_count,
        )

    async def get_history(self, application_id: UUID, principal: Principal) -> list[ApplicationHistoryEvent]:
        application = await self._get_application(application_id, principal)
        return list(await self.history.list_events_for_application(application.id))

    async def get_application(self, application_id: UUID, principal: Principal) -> Application:
        return await self._get_application(application_id, principal)
