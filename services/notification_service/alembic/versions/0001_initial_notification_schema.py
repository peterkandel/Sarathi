"""initial notification schema

Revision ID: 0001_initial_notification_schema
Revises:
Create Date: 2026-06-21 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_notification_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_templates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("template_code", sa.String(length=120), nullable=False),
        sa.Column("template_name", sa.String(length=255), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("subject_template", sa.String(length=255), nullable=True),
        sa.Column("body_template", sa.Text(), nullable=False),
        sa.Column("push_title_template", sa.String(length=255), nullable=True),
        sa.Column("push_body_template", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("template_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("template_code", "version_number", "deleted_at", name="uq_notification_templates_code_version_deleted_at"),
    )
    op.create_index("ix_notification_templates_template_code", "notification_templates", ["template_code"], unique=False)
    op.create_index("ix_notification_templates_channel", "notification_templates", ["channel"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("template_id", sa.Uuid(), sa.ForeignKey("notification_templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recipient_subject", sa.String(length=120), nullable=False),
        sa.Column("recipient_contact", sa.String(length=255), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("category_code", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("rendered_context", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_retry_count", sa.Integer(), nullable=False),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("delivery_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notifications_recipient_subject", "notifications", ["recipient_subject"], unique=False)
    op.create_index("ix_notifications_channel", "notifications", ["channel"], unique=False)
    op.create_index("ix_notifications_category_code", "notifications", ["category_code"], unique=False)
    op.create_index("ix_notifications_scheduled_for", "notifications", ["scheduled_for"], unique=False)
    op.create_index("ix_notifications_next_retry_at", "notifications", ["next_retry_at"], unique=False)

    op.create_table(
        "notification_queue_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("notification_id", sa.Uuid(), sa.ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("worker_id", sa.String(length=120), nullable=True),
        sa.Column("correlation_id", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notification_queue_items_notification_id", "notification_queue_items", ["notification_id"], unique=False)
    op.create_index("ix_notification_queue_items_channel", "notification_queue_items", ["channel"], unique=False)
    op.create_index("ix_notification_queue_items_status", "notification_queue_items", ["status"], unique=False)
    op.create_index("ix_notification_queue_items_available_at", "notification_queue_items", ["available_at"], unique=False)
    op.create_index("ix_notification_queue_items_next_retry_at", "notification_queue_items", ["next_retry_at"], unique=False)

    op.create_table(
        "notification_delivery_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("notification_id", sa.Uuid(), sa.ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("queue_item_id", sa.Uuid(), sa.ForeignKey("notification_queue_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("provider_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("request_payload", sa.JSON(), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notification_delivery_attempts_notification_id", "notification_delivery_attempts", ["notification_id"], unique=False)
    op.create_index("ix_notification_delivery_attempts_queue_item_id", "notification_delivery_attempts", ["queue_item_id"], unique=False)
    op.create_index("ix_notification_delivery_attempts_channel", "notification_delivery_attempts", ["channel"], unique=False)
    op.create_index("ix_notification_delivery_attempts_status", "notification_delivery_attempts", ["status"], unique=False)

    op.create_table(
        "notification_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("notification_id", sa.Uuid(), sa.ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("old_status", sa.String(length=32), nullable=True),
        sa.Column("new_status", sa.String(length=32), nullable=True),
        sa.Column("actor_subject", sa.String(length=120), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notification_events_notification_id", "notification_events", ["notification_id"], unique=False)
    op.create_index("ix_notification_events_event_type", "notification_events", ["event_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notification_events_event_type", table_name="notification_events")
    op.drop_index("ix_notification_events_notification_id", table_name="notification_events")
    op.drop_table("notification_events")
    op.drop_index("ix_notification_delivery_attempts_status", table_name="notification_delivery_attempts")
    op.drop_index("ix_notification_delivery_attempts_channel", table_name="notification_delivery_attempts")
    op.drop_index("ix_notification_delivery_attempts_queue_item_id", table_name="notification_delivery_attempts")
    op.drop_index("ix_notification_delivery_attempts_notification_id", table_name="notification_delivery_attempts")
    op.drop_table("notification_delivery_attempts")
    op.drop_index("ix_notification_queue_items_next_retry_at", table_name="notification_queue_items")
    op.drop_index("ix_notification_queue_items_available_at", table_name="notification_queue_items")
    op.drop_index("ix_notification_queue_items_status", table_name="notification_queue_items")
    op.drop_index("ix_notification_queue_items_channel", table_name="notification_queue_items")
    op.drop_index("ix_notification_queue_items_notification_id", table_name="notification_queue_items")
    op.drop_table("notification_queue_items")
    op.drop_index("ix_notifications_next_retry_at", table_name="notifications")
    op.drop_index("ix_notifications_scheduled_for", table_name="notifications")
    op.drop_index("ix_notifications_category_code", table_name="notifications")
    op.drop_index("ix_notifications_channel", table_name="notifications")
    op.drop_index("ix_notifications_recipient_subject", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_notification_templates_channel", table_name="notification_templates")
    op.drop_index("ix_notification_templates_template_code", table_name="notification_templates")
    op.drop_table("notification_templates")
