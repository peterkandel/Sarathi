"""initial integration schema

Revision ID: 0001_initial_integration_schema
Revises:
Create Date: 2026-06-21 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_integration_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_adapters",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("adapter_code", sa.String(length=120), nullable=False),
        sa.Column("adapter_name", sa.String(length=255), nullable=False),
        sa.Column("system_code", sa.String(length=120), nullable=False),
        sa.Column("adapter_type", sa.String(length=32), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("auth_type", sa.String(length=64), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("max_retry_attempts", sa.Integer(), nullable=False),
        sa.Column("breaker_failure_threshold", sa.Integer(), nullable=False),
        sa.Column("breaker_reset_seconds", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("adapter_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("adapter_code", "deleted_at", name="uq_integration_adapters_code_deleted_at"),
    )
    op.create_index("ix_integration_adapters_adapter_code", "integration_adapters", ["adapter_code"], unique=False)
    op.create_index("ix_integration_adapters_system_code", "integration_adapters", ["system_code"], unique=False)
    op.create_index("ix_integration_adapters_adapter_type", "integration_adapters", ["adapter_type"], unique=False)

    op.create_table(
        "integration_circuit_breakers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("adapter_id", sa.Uuid(), sa.ForeignKey("integration_adapters.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("half_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=120), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("reset_after_seconds", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_integration_circuit_breakers_adapter_id", "integration_circuit_breakers", ["adapter_id"], unique=True)

    op.create_table(
        "integration_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("adapter_id", sa.Uuid(), sa.ForeignKey("integration_adapters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("system_code", sa.String(length=120), nullable=False),
        sa.Column("operation_code", sa.String(length=120), nullable=False),
        sa.Column("idempotency_key", sa.String(length=120), nullable=False),
        sa.Column("correlation_id", sa.String(length=120), nullable=True),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        sa.Column("canonical_payload", sa.JSON(), nullable=False),
        sa.Column("request_payload", sa.JSON(), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=120), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("queue_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_integration_requests_adapter_id", "integration_requests", ["adapter_id"], unique=False)
    op.create_index("ix_integration_requests_system_code", "integration_requests", ["system_code"], unique=False)
    op.create_index("ix_integration_requests_operation_code", "integration_requests", ["operation_code"], unique=False)
    op.create_index("ix_integration_requests_idempotency_key", "integration_requests", ["idempotency_key"], unique=False)
    op.create_index("ix_integration_requests_status", "integration_requests", ["status"], unique=False)
    op.create_index("ix_integration_requests_next_retry_at", "integration_requests", ["next_retry_at"], unique=False)

    op.create_table(
        "integration_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_id", sa.Uuid(), sa.ForeignKey("integration_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("adapter_code", sa.String(length=120), nullable=False),
        sa.Column("provider_name", sa.String(length=120), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("error_class", sa.String(length=120), nullable=True),
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
    op.create_index("ix_integration_attempts_request_id", "integration_attempts", ["request_id"], unique=False)
    op.create_index("ix_integration_attempts_status", "integration_attempts", ["status"], unique=False)
    op.create_index("ix_integration_attempts_adapter_code", "integration_attempts", ["adapter_code"], unique=False)

    op.create_table(
        "integration_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_id", sa.Uuid(), sa.ForeignKey("integration_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("old_status", sa.String(length=32), nullable=True),
        sa.Column("new_status", sa.String(length=32), nullable=True),
        sa.Column("publication_status", sa.String(length=32), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("channel", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_integration_events_request_id", "integration_events", ["request_id"], unique=False)
    op.create_index("ix_integration_events_event_type", "integration_events", ["event_type"], unique=False)
    op.create_index("ix_integration_events_publication_status", "integration_events", ["publication_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_integration_events_publication_status", table_name="integration_events")
    op.drop_index("ix_integration_events_event_type", table_name="integration_events")
    op.drop_index("ix_integration_events_request_id", table_name="integration_events")
    op.drop_table("integration_events")
    op.drop_index("ix_integration_attempts_adapter_code", table_name="integration_attempts")
    op.drop_index("ix_integration_attempts_status", table_name="integration_attempts")
    op.drop_index("ix_integration_attempts_request_id", table_name="integration_attempts")
    op.drop_table("integration_attempts")
    op.drop_index("ix_integration_requests_next_retry_at", table_name="integration_requests")
    op.drop_index("ix_integration_requests_status", table_name="integration_requests")
    op.drop_index("ix_integration_requests_idempotency_key", table_name="integration_requests")
    op.drop_index("ix_integration_requests_operation_code", table_name="integration_requests")
    op.drop_index("ix_integration_requests_system_code", table_name="integration_requests")
    op.drop_index("ix_integration_requests_adapter_id", table_name="integration_requests")
    op.drop_table("integration_requests")
    op.drop_index("ix_integration_circuit_breakers_adapter_id", table_name="integration_circuit_breakers")
    op.drop_table("integration_circuit_breakers")
    op.drop_index("ix_integration_adapters_adapter_type", table_name="integration_adapters")
    op.drop_index("ix_integration_adapters_system_code", table_name="integration_adapters")
    op.drop_index("ix_integration_adapters_adapter_code", table_name="integration_adapters")
    op.drop_table("integration_adapters")
