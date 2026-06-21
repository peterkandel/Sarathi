from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"
    ARCHIVED = "archived"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationTemplate(Base, TimestampMixin):
    __tablename__ = "notification_templates"
    __table_args__ = (UniqueConstraint("template_code", "version_number", "deleted_at", name="uq_notification_templates_code_version_deleted_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    template_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    subject_template: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    push_title_template: Mapped[str | None] = mapped_column(String(255), nullable=True)
    push_body_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    template_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    notifications: Mapped[list[Notification]] = relationship("Notification", back_populates="template")


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    template_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("notification_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    recipient_subject: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    recipient_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    category_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    rendered_context: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=NotificationStatus.QUEUED.value)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivery_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    template: Mapped[NotificationTemplate | None] = relationship("NotificationTemplate", back_populates="notifications")
    queue_items: Mapped[list[NotificationQueueItem]] = relationship("NotificationQueueItem", back_populates="notification", cascade="all, delete-orphan")
    delivery_attempts: Mapped[list[NotificationDeliveryAttempt]] = relationship("NotificationDeliveryAttempt", back_populates="notification", cascade="all, delete-orphan")
    events: Mapped[list[NotificationEvent]] = relationship("NotificationEvent", back_populates="notification", cascade="all, delete-orphan")


class NotificationQueueItem(Base, TimestampMixin):
    __tablename__ = "notification_queue_items"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    notification_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=DeliveryStatus.PENDING.value, index=True)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(120), nullable=True)

    notification: Mapped[Notification] = relationship("Notification", back_populates="queue_items")
    delivery_attempts: Mapped[list[NotificationDeliveryAttempt]] = relationship("NotificationDeliveryAttempt", back_populates="queue_item", cascade="all, delete-orphan")


class NotificationDeliveryAttempt(Base, TimestampMixin):
    __tablename__ = "notification_delivery_attempts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    notification_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True)
    queue_item_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("notification_queue_items.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    response_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    notification: Mapped[Notification] = relationship("Notification", back_populates="delivery_attempts")
    queue_item: Mapped[NotificationQueueItem] = relationship("NotificationQueueItem", back_populates="delivery_attempts")


class NotificationEvent(Base, TimestampMixin):
    __tablename__ = "notification_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    notification_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    old_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    actor_subject: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    notification: Mapped[Notification] = relationship("Notification", back_populates="events")
