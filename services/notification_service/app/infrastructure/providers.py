from __future__ import annotations

from dataclasses import dataclass

from app.domain.models import Notification, NotificationQueueItem, NotificationTemplate
from app.domain.ports import NotificationDeliveryResult, NotificationProviderProtocol


@dataclass(slots=True)
class BaseNotificationProvider(NotificationProviderProtocol):
    provider_name: str

    async def deliver(self, notification: Notification, template: NotificationTemplate, queue_item: NotificationQueueItem, attempt_no: int) -> NotificationDeliveryResult:
        simulate_failures = int(notification.rendered_context.get("simulate_failure_attempts", 0) or 0)
        if attempt_no <= simulate_failures:
            return NotificationDeliveryResult(
                success=False,
                error_code="SIMULATED_DELIVERY_FAILURE",
                error_message=f"Simulated delivery failure for attempt {attempt_no}",
                response_payload={"attempt_no": attempt_no, "channel": notification.channel, "provider": self.provider_name},
            )
        message_id = f"{self.provider_name}-{notification.id}-{attempt_no}"
        return NotificationDeliveryResult(
            success=True,
            provider_message_id=message_id,
            response_payload={"attempt_no": attempt_no, "channel": notification.channel, "provider": self.provider_name, "template_code": template.template_code},
        )


class EmailNotificationProvider(BaseNotificationProvider):
    def __init__(self) -> None:
        super().__init__(provider_name="email_provider")


class SmsNotificationProvider(BaseNotificationProvider):
    def __init__(self) -> None:
        super().__init__(provider_name="sms_provider")


class PushNotificationProvider(BaseNotificationProvider):
    def __init__(self) -> None:
        super().__init__(provider_name="push_provider")


class NotificationProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, NotificationProviderProtocol] = {
            "email": EmailNotificationProvider(),
            "sms": SmsNotificationProvider(),
            "push": PushNotificationProvider(),
        }

    def resolve(self, channel: str) -> NotificationProviderProtocol:
        provider = self._providers.get(channel.lower())
        if provider is None:
            raise ValueError(f"Unsupported notification channel: {channel}")
        return provider


provider_registry = NotificationProviderRegistry()
