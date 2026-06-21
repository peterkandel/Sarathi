from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import NotificationService
from app.infrastructure.db import get_session
from app.infrastructure.repositories import NotificationDeliveryRepository, NotificationEventRepository, NotificationQueueRepository, NotificationRepository, NotificationTemplateRepository


async def get_template_repository(session: AsyncSession = Depends(get_session)) -> NotificationTemplateRepository:
    return NotificationTemplateRepository(session)


async def get_notification_repository(session: AsyncSession = Depends(get_session)) -> NotificationRepository:
    return NotificationRepository(session)


async def get_queue_repository(session: AsyncSession = Depends(get_session)) -> NotificationQueueRepository:
    return NotificationQueueRepository(session)


async def get_delivery_repository(session: AsyncSession = Depends(get_session)) -> NotificationDeliveryRepository:
    return NotificationDeliveryRepository(session)


async def get_event_repository(session: AsyncSession = Depends(get_session)) -> NotificationEventRepository:
    return NotificationEventRepository(session)


async def get_notification_service(
    template_repository: NotificationTemplateRepository = Depends(get_template_repository),
    notification_repository: NotificationRepository = Depends(get_notification_repository),
    queue_repository: NotificationQueueRepository = Depends(get_queue_repository),
    delivery_repository: NotificationDeliveryRepository = Depends(get_delivery_repository),
    event_repository: NotificationEventRepository = Depends(get_event_repository),
) -> NotificationService:
    return NotificationService(template_repository, notification_repository, queue_repository, delivery_repository, event_repository)
