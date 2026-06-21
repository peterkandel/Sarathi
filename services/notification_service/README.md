# Notification Service

FastAPI service for official citizen notifications with templates, queued delivery, retries, and delivery tracking.

## Architecture

Notifications are template-driven and channel-aware. Incoming notification requests are converted into persisted notification records, queue items, delivery attempts, and event history. A queue processor handles retries and delivery state transitions.

## API

- `POST /notifications/v1/templates`
- `GET /notifications/v1/templates`
- `GET /notifications/v1/templates/{template_id}`
- `POST /notifications/v1/notifications`
- `GET /notifications/v1/notifications`
- `GET /notifications/v1/notifications/{notification_id}`
- `POST /notifications/v1/notifications/{notification_id}/read`
- `POST /notifications/v1/notifications/{notification_id}/archive`
- `GET /notifications/v1/notifications/{notification_id}/attempts`
- `GET /notifications/v1/notifications/{notification_id}/events`
- `GET /notifications/v1/summary`
- `GET /notifications/v1/unread-count`
- `POST /notifications/v1/queue/process`

## Notes

- Supported channels are email, SMS, and push notifications.
- Queue processing records delivery attempts and retry outcomes.
- Delivery tracking is persisted per notification and per queue item for auditability.
