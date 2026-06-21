from __future__ import annotations

from datetime import datetime, timezone, timedelta
from string import Formatter
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.domain.events import NotificationEventPayload
from app.domain.models import DeliveryStatus, Notification, NotificationChannel, NotificationDeliveryAttempt, NotificationEvent, NotificationQueueItem, NotificationStatus, NotificationTemplate
from app.domain.ports import NotificationDeliveryRepositoryProtocol, NotificationEventRepositoryProtocol, NotificationProviderProtocol, NotificationQueueRepositoryProtocol, NotificationRepositoryProtocol, NotificationTemplateRepositoryProtocol
from app.domain.schemas import NotificationCreate, NotificationDeliveryAttemptRead, NotificationEventRead, NotificationQueueItemRead, NotificationRead, NotificationSummary, NotificationTemplateCreate, NotificationTemplateRead, QueueProcessResult
from shared_auth import Role
from shared_auth.models import Principal
from shared_auth.security import has_any_role

from app.infrastructure.providers import provider_registry


ADMIN_ROLES = (Role.ADMINISTRATOR, Role.SUPER_ADMINISTRATOR)


class SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


class NotificationService:
    def __init__(
        self,
        templates: NotificationTemplateRepositoryProtocol,
        notifications: NotificationRepositoryProtocol,
        queue_items: NotificationQueueRepositoryProtocol,
        attempts: NotificationDeliveryRepositoryProtocol,
        events: NotificationEventRepositoryProtocol,
    ) -> None:
        self.templates = templates
        self.notifications = notifications
        self.queue_items = queue_items
        self.attempts = attempts
        self.events = events
        self.providers = provider_registry

    def _is_admin(self, principal: Principal) -> bool:
        return has_any_role(principal, ADMIN_ROLES)

    def _require_admin(self, principal: Principal) -> None:
        if not self._is_admin(principal):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrative role required")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _render(self, template: str | None, context: dict[str, object]) -> str | None:
        if template is None:
            return None
        safe_context = SafeFormatDict({key: self._stringify(value) for key, value in context.items()})
        return Formatter().vformat(template, (), safe_context)

    def _stringify(self, value: object) -> object:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    async def create_template(self, payload: NotificationTemplateCreate, principal: Principal) -> NotificationTemplate:
        self._require_admin(principal)
        template = NotificationTemplate(
            template_code=payload.template_code,
            template_name=payload.template_name,
            channel=payload.channel.lower(),
            version_number=payload.version_number,
            subject_template=payload.subject_template,
            body_template=payload.body_template,
            push_title_template=payload.push_title_template,
            push_body_template=payload.push_body_template,
            enabled=payload.enabled,
            template_metadata=payload.template_metadata,
        )
        created = await self.templates.create_template(template)
        await self.events.create_event(NotificationEventPayload(notification_id=created.id, event_type="NotificationTemplateCreated", actor_subject=principal.subject, payload={"template_code": created.template_code, "channel": created.channel}))
        return created

    async def list_templates(self, principal: Principal) -> list[NotificationTemplate]:
        self._require_admin(principal)
        return list(await self.templates.list_templates())

    async def get_template(self, template_id: UUID, principal: Principal) -> NotificationTemplate:
        self._require_admin(principal)
        template = await self.templates.get_template_by_id(template_id)
        if template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification template not found")
        return template

    async def create_notification(self, payload: NotificationCreate, principal: Principal) -> Notification:
        self._require_admin(principal)
        template = await self.templates.get_template_by_code(payload.template_code, payload.template_version)
        if template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification template not found")
        channel = payload.channel.lower() or template.channel
        if channel != template.channel:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Template channel does not match requested notification channel")
        context = {**payload.context, "recipient_subject": payload.recipient_subject, "channel": channel, "template_code": template.template_code, "notification_id": str(uuid4())}
        title = payload.title or self._render(template.subject_template, context) or template.template_name
        body = self._render(template.body_template, context) or ""
        scheduled_for = payload.scheduled_for or self._now()
        notification = Notification(
            template_id=template.id,
            recipient_subject=payload.recipient_subject,
            recipient_contact=payload.recipient_contact,
            channel=channel,
            category_code=payload.category_code,
            title=title,
            body=body,
            rendered_context=context,
            status=NotificationStatus.QUEUED.value,
            priority=payload.priority,
            scheduled_for=scheduled_for,
            max_retry_count=payload.max_retry_count,
            next_retry_at=scheduled_for,
        )
        created = await self.notifications.create_notification(notification)
        context["notification_id"] = str(created.id)
        created.rendered_context = context
        queue_item = NotificationQueueItem(
            notification_id=created.id,
            channel=channel,
            status=DeliveryStatus.PENDING.value,
            available_at=scheduled_for,
            attempt_count=0,
            max_attempts=payload.max_retry_count,
            next_retry_at=scheduled_for,
        )
        await self.queue_items.create_queue_item(queue_item)
        await self.events.create_event(NotificationEventPayload(notification_id=created.id, event_type="NotificationCreated", actor_subject=principal.subject, payload={"channel": channel, "template_code": template.template_code}))
        return created

    async def list_notifications(self, principal: Principal) -> list[Notification]:
        if self._is_admin(principal):
            return list(await self.notifications.list_notifications_for_subject(principal.subject))
        return list(await self.notifications.list_notifications_for_subject(principal.subject))

    async def get_notification(self, notification_id: UUID, principal: Principal) -> Notification:
        notification = await self.notifications.get_notification_by_id(notification_id)
        if notification is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        if notification.recipient_subject != principal.subject and not self._is_admin(principal):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Notification access denied")
        return notification

    async def mark_read(self, notification_id: UUID, principal: Principal) -> Notification:
        notification = await self.get_notification(notification_id, principal)
        now = self._now()
        old_status = notification.status
        notification.status = NotificationStatus.READ.value
        notification.read_at = now
        await self.events.create_event(NotificationEventPayload(notification_id=notification.id, event_type="NotificationRead", old_status=old_status, new_status=notification.status, actor_subject=principal.subject))
        return notification

    async def archive(self, notification_id: UUID, principal: Principal) -> Notification:
        notification = await self.get_notification(notification_id, principal)
        now = self._now()
        old_status = notification.status
        notification.status = NotificationStatus.ARCHIVED.value
        notification.archived_at = now
        await self.events.create_event(NotificationEventPayload(notification_id=notification.id, event_type="NotificationArchived", old_status=old_status, new_status=notification.status, actor_subject=principal.subject))
        return notification

    async def process_queue(self, limit: int, principal: Principal) -> QueueProcessResult:
        self._require_admin(principal)
        due_items = await self.queue_items.list_due_queue_items(limit)
        processed = delivered = failed = retried = 0
        for queue_item in due_items:
            processed += 1
            notification = await self.get_notification(queue_item.notification_id, principal)
            template = await self.templates.get_template_by_id(notification.template_id) if notification.template_id else None
            if template is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Notification template missing")
            now = self._now()
            queue_item.status = DeliveryStatus.PROCESSING.value
            queue_item.locked_at = now
            queue_item.attempt_count += 1
            attempt_no = queue_item.attempt_count
            notification.status = NotificationStatus.PROCESSING.value
            attempt = NotificationDeliveryAttempt(
                notification_id=notification.id,
                queue_item_id=queue_item.id,
                channel=notification.channel,
                attempt_no=attempt_no,
                provider_name=self.providers.resolve(notification.channel).provider_name,
                status=DeliveryStatus.PROCESSING.value,
                request_payload={"channel": notification.channel, "title": notification.title, "body": notification.body, "context": notification.rendered_context},
                response_payload={},
                started_at=now,
            )
            await self.attempts.create_attempt(attempt)
            provider = self.providers.resolve(notification.channel)
            result = await provider.deliver(notification, template, queue_item, attempt_no)
            attempt.completed_at = self._now()
            if result.success:
                delivered += 1
                attempt.status = DeliveryStatus.DELIVERED.value
                attempt.provider_message_id = result.provider_message_id
                attempt.response_payload = result.response_payload or {}
                notification.status = NotificationStatus.DELIVERED.value
                notification.sent_at = now
                notification.delivered_at = self._now()
                notification.last_error = None
                queue_item.status = DeliveryStatus.DELIVERED.value
                queue_item.processed_at = self._now()
                queue_item.last_error = None
                queue_item.next_retry_at = None
                await self.events.create_event(NotificationEventPayload(notification_id=notification.id, event_type="NotificationDelivered", old_status=NotificationStatus.PROCESSING.value, new_status=notification.status, actor_subject=principal.subject, payload={"provider_message_id": result.provider_message_id or ""}))
            else:
                failed += 1
                attempt.status = DeliveryStatus.FAILED.value
                attempt.error_code = result.error_code
                attempt.error_message = result.error_message
                attempt.response_payload = result.response_payload or {}
                notification.last_error = result.error_message
                notification.retry_count += 1
                queue_item.last_error = result.error_message
                queue_item.next_retry_at = self._now()
                retry_allowed = queue_item.attempt_count < queue_item.max_attempts
                if retry_allowed:
                    retried += 1
                    queue_item.status = DeliveryStatus.RETRYING.value
                    notification.status = NotificationStatus.QUEUED.value
                    notification.next_retry_at = queue_item.next_retry_at
                else:
                    queue_item.status = DeliveryStatus.FAILED.value
                    queue_item.processed_at = self._now()
                    notification.status = NotificationStatus.FAILED.value
                    notification.next_retry_at = None
                await self.events.create_event(NotificationEventPayload(notification_id=notification.id, event_type="NotificationDeliveryFailed", old_status=NotificationStatus.PROCESSING.value, new_status=notification.status, actor_subject=principal.subject, payload={"error_code": result.error_code or "", "error_message": result.error_message or ""}))
        return QueueProcessResult(processed=processed, delivered=delivered, failed=failed, retried=retried)

    async def get_delivery_attempts(self, notification_id: UUID, principal: Principal) -> list[NotificationDeliveryAttempt]:
        notification = await self.get_notification(notification_id, principal)
        attempts = await self.attempts.list_attempts_for_notification(notification.id)
        return list(attempts)

    async def get_events(self, notification_id: UUID, principal: Principal) -> list[NotificationEvent]:
        notification = await self.get_notification(notification_id, principal)
        events = await self.events.list_events_for_notification(notification.id)
        return list(events)

    async def summary(self, principal: Principal) -> NotificationSummary:
        notifications = await self.list_notifications(principal)
        unread_count = len([item for item in notifications if item.status not in {NotificationStatus.READ.value, NotificationStatus.ARCHIVED.value}])
        queued_count = len([item for item in notifications if item.status == NotificationStatus.QUEUED.value])
        delivered_count = len([item for item in notifications if item.status == NotificationStatus.DELIVERED.value])
        failed_count = len([item for item in notifications if item.status == NotificationStatus.FAILED.value])
        return NotificationSummary(total_notifications=len(notifications), unread_count=unread_count, queued_count=queued_count, delivered_count=delivered_count, failed_count=failed_count)
