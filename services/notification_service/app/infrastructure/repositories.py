from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import NotificationEventPayload
from app.domain.models import DeliveryStatus, Notification, NotificationDeliveryAttempt, NotificationEvent, NotificationQueueItem, NotificationStatus, NotificationTemplate


class NotificationTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_template(self, template: NotificationTemplate) -> NotificationTemplate:
        self.session.add(template)
        await self.session.flush()
        return template

    async def get_template_by_id(self, template_id: UUID) -> NotificationTemplate | None:
        result = await self.session.execute(select(NotificationTemplate).where(NotificationTemplate.id == template_id, NotificationTemplate.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def get_template_by_code(self, template_code: str, version_number: int | None = None) -> NotificationTemplate | None:
        query = select(NotificationTemplate).where(NotificationTemplate.template_code == template_code, NotificationTemplate.deleted_at.is_(None))
        if version_number is not None:
            query = query.where(NotificationTemplate.version_number == version_number)
        query = query.order_by(NotificationTemplate.version_number.desc())
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_templates(self) -> Sequence[NotificationTemplate]:
        result = await self.session.execute(select(NotificationTemplate).where(NotificationTemplate.deleted_at.is_(None)).order_by(NotificationTemplate.created_at.desc()))
        return list(result.scalars().all())


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_notification(self, notification: Notification) -> Notification:
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def get_notification_by_id(self, notification_id: UUID) -> Notification | None:
        result = await self.session.execute(select(Notification).where(Notification.id == notification_id, Notification.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def list_notifications_for_subject(self, recipient_subject: str) -> Sequence[Notification]:
        result = await self.session.execute(select(Notification).where(Notification.recipient_subject == recipient_subject, Notification.deleted_at.is_(None)).order_by(Notification.created_at.desc()))
        return list(result.scalars().all())

    async def count_notifications_for_subject(self, recipient_subject: str) -> int:
        result = await self.session.execute(select(func.count()).select_from(Notification).where(Notification.recipient_subject == recipient_subject, Notification.deleted_at.is_(None)))
        return int(result.scalar_one())

    async def count_unread_notifications_for_subject(self, recipient_subject: str) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.recipient_subject == recipient_subject,
                Notification.deleted_at.is_(None),
                Notification.status.notin_([NotificationStatus.READ.value, NotificationStatus.ARCHIVED.value]),
            )
        )
        return int(result.scalar_one())


class NotificationQueueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_queue_item(self, queue_item: NotificationQueueItem) -> NotificationQueueItem:
        self.session.add(queue_item)
        await self.session.flush()
        return queue_item

    async def list_due_queue_items(self, limit: int) -> Sequence[NotificationQueueItem]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(NotificationQueueItem)
            .where(
                NotificationQueueItem.deleted_at.is_(None),
                NotificationQueueItem.status.in_([DeliveryStatus.PENDING.value, DeliveryStatus.RETRYING.value]),
                NotificationQueueItem.available_at <= now,
                or_(NotificationQueueItem.next_retry_at.is_(None), NotificationQueueItem.next_retry_at <= now),
            )
            .order_by(NotificationQueueItem.available_at.asc(), NotificationQueueItem.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_queue_items_for_notification(self, notification_id: UUID) -> Sequence[NotificationQueueItem]:
        result = await self.session.execute(select(NotificationQueueItem).where(NotificationQueueItem.notification_id == notification_id, NotificationQueueItem.deleted_at.is_(None)).order_by(NotificationQueueItem.created_at.asc()))
        return list(result.scalars().all())


class NotificationDeliveryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_attempt(self, attempt: NotificationDeliveryAttempt) -> NotificationDeliveryAttempt:
        self.session.add(attempt)
        await self.session.flush()
        return attempt

    async def list_attempts_for_notification(self, notification_id: UUID) -> Sequence[NotificationDeliveryAttempt]:
        result = await self.session.execute(select(NotificationDeliveryAttempt).where(NotificationDeliveryAttempt.notification_id == notification_id, NotificationDeliveryAttempt.deleted_at.is_(None)).order_by(NotificationDeliveryAttempt.attempt_no.asc()))
        return list(result.scalars().all())


class NotificationEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_event(self, event: NotificationEventPayload) -> NotificationEvent:
        notification_event = NotificationEvent(
            notification_id=event.notification_id,
            event_type=event.event_type,
            old_status=event.old_status,
            new_status=event.new_status,
            actor_subject=event.actor_subject,
            payload=event.payload,
        )
        self.session.add(notification_event)
        await self.session.flush()
        return notification_event

    async def list_events_for_notification(self, notification_id: UUID) -> Sequence[NotificationEvent]:
        result = await self.session.execute(select(NotificationEvent).where(NotificationEvent.notification_id == notification_id, NotificationEvent.deleted_at.is_(None)).order_by(NotificationEvent.created_at.asc()))
        return list(result.scalars().all())
