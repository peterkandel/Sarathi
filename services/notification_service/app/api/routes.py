from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import get_notification_service
from app.application.services import NotificationService
from app.domain.schemas import MessageResponse, NotificationCreate, NotificationDeliveryAttemptRead, NotificationEventRead, NotificationQueueItemRead, NotificationRead, NotificationSummary, NotificationTemplateCreate, NotificationTemplateRead, QueueProcessResult
from shared_auth import get_principal


router = APIRouter(tags=["notifications"])


@router.post("/templates", response_model=NotificationTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(request: Request, payload: NotificationTemplateCreate, service: NotificationService = Depends(get_notification_service)) -> NotificationTemplateRead:
    template = await service.create_template(payload, get_principal(request))
    return NotificationTemplateRead.model_validate(template, from_attributes=True)


@router.get("/templates", response_model=list[NotificationTemplateRead])
async def list_templates(request: Request, service: NotificationService = Depends(get_notification_service)) -> list[NotificationTemplateRead]:
    templates = await service.list_templates(get_principal(request))
    return [NotificationTemplateRead.model_validate(template, from_attributes=True) for template in templates]


@router.get("/templates/{template_id}", response_model=NotificationTemplateRead)
async def get_template(template_id: UUID, request: Request, service: NotificationService = Depends(get_notification_service)) -> NotificationTemplateRead:
    template = await service.get_template(template_id, get_principal(request))
    return NotificationTemplateRead.model_validate(template, from_attributes=True)


@router.post("/notifications", response_model=NotificationRead, status_code=status.HTTP_201_CREATED)
async def create_notification(request: Request, payload: NotificationCreate, service: NotificationService = Depends(get_notification_service)) -> NotificationRead:
    notification = await service.create_notification(payload, get_principal(request))
    return NotificationRead.model_validate(notification, from_attributes=True)


@router.get("/notifications", response_model=list[NotificationRead])
async def list_notifications(request: Request, service: NotificationService = Depends(get_notification_service)) -> list[NotificationRead]:
    notifications = await service.list_notifications(get_principal(request))
    return [NotificationRead.model_validate(notification, from_attributes=True) for notification in notifications]


@router.get("/notifications/{notification_id}", response_model=NotificationRead)
async def get_notification(notification_id: UUID, request: Request, service: NotificationService = Depends(get_notification_service)) -> NotificationRead:
    notification = await service.get_notification(notification_id, get_principal(request))
    return NotificationRead.model_validate(notification, from_attributes=True)


@router.post("/notifications/{notification_id}/read", response_model=NotificationRead)
async def mark_read(notification_id: UUID, request: Request, service: NotificationService = Depends(get_notification_service)) -> NotificationRead:
    notification = await service.mark_read(notification_id, get_principal(request))
    return NotificationRead.model_validate(notification, from_attributes=True)


@router.post("/notifications/{notification_id}/archive", response_model=NotificationRead)
async def archive(notification_id: UUID, request: Request, service: NotificationService = Depends(get_notification_service)) -> NotificationRead:
    notification = await service.archive(notification_id, get_principal(request))
    return NotificationRead.model_validate(notification, from_attributes=True)


@router.get("/notifications/{notification_id}/attempts", response_model=list[NotificationDeliveryAttemptRead])
async def list_attempts(notification_id: UUID, request: Request, service: NotificationService = Depends(get_notification_service)) -> list[NotificationDeliveryAttemptRead]:
    attempts = await service.get_delivery_attempts(notification_id, get_principal(request))
    return [NotificationDeliveryAttemptRead.model_validate(attempt, from_attributes=True) for attempt in attempts]


@router.get("/notifications/{notification_id}/events", response_model=list[NotificationEventRead])
async def list_events(notification_id: UUID, request: Request, service: NotificationService = Depends(get_notification_service)) -> list[NotificationEventRead]:
    events = await service.get_events(notification_id, get_principal(request))
    return [NotificationEventRead.model_validate(event, from_attributes=True) for event in events]


@router.get("/summary", response_model=NotificationSummary)
async def summary(request: Request, service: NotificationService = Depends(get_notification_service)) -> NotificationSummary:
    return await service.summary(get_principal(request))


@router.get("/unread-count")
async def unread_count(request: Request, service: NotificationService = Depends(get_notification_service)) -> dict[str, int]:
    summary = await service.summary(get_principal(request))
    return {"unread_count": summary.unread_count}


@router.post("/queue/process", response_model=QueueProcessResult)
async def process_queue(request: Request, limit: int = 20, service: NotificationService = Depends(get_notification_service)) -> QueueProcessResult:
    return await service.process_queue(limit, get_principal(request))


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "notification_service"}
