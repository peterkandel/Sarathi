"""initial application schema

Revision ID: 0001_initial_application_schema
Revises:
Create Date: 2026-06-21 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Uuid


revision = "0001_initial_application_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", Uuid(), primary_key=True),
        sa.Column("reference_number", sa.String(length=40), nullable=False),
        sa.Column("applicant_subject", sa.String(length=120), nullable=False),
        sa.Column("workflow_definition_code", sa.String(length=120), nullable=False),
        sa.Column("workflow_definition_version", sa.String(length=32), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("application_status", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("application_metadata", sa.JSON(), nullable=False),
        sa.Column("workflow_application_id", Uuid(), nullable=True),
        sa.Column("workflow_status", sa.String(length=32), nullable=True),
        sa.Column("workflow_current_state_id", Uuid(), nullable=True),
        sa.Column("workflow_current_state_code", sa.String(length=120), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_subject", sa.String(length=120), nullable=True),
        sa.Column("updated_by_subject", sa.String(length=120), nullable=True),
        sa.UniqueConstraint("reference_number", "deleted_at", name="uq_applications_reference_number_deleted_at"),
    )
    op.create_index("ix_applications_reference_number", "applications", ["reference_number"], unique=False)
    op.create_index("ix_applications_applicant_subject", "applications", ["applicant_subject"], unique=False)
    op.create_index("ix_applications_workflow_application_id", "applications", ["workflow_application_id"], unique=False)
    op.create_index("ix_applications_workflow_current_state_id", "applications", ["workflow_current_state_id"], unique=False)

    op.create_table(
        "application_documents",
        sa.Column("id", Uuid(), primary_key=True),
        sa.Column("application_id", Uuid(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("document_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_subject", sa.String(length=120), nullable=True),
        sa.Column("updated_by_subject", sa.String(length=120), nullable=True),
        sa.UniqueConstraint("application_id", "storage_key", "deleted_at", name="uq_application_documents_application_storage_deleted_at"),
    )
    op.create_index("ix_application_documents_application_id", "application_documents", ["application_id"], unique=False)
    op.create_index("ix_application_documents_storage_key", "application_documents", ["storage_key"], unique=False)

    op.create_table(
        "application_history_events",
        sa.Column("id", Uuid(), primary_key=True),
        sa.Column("application_id", Uuid(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("recorded_by_subject", sa.String(length=120), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_application_history_events_application_id", "application_history_events", ["application_id"], unique=False)
    op.create_index("ix_application_history_events_event_type", "application_history_events", ["event_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_application_history_events_event_type", table_name="application_history_events")
    op.drop_index("ix_application_history_events_application_id", table_name="application_history_events")
    op.drop_table("application_history_events")
    op.drop_index("ix_application_documents_storage_key", table_name="application_documents")
    op.drop_index("ix_application_documents_application_id", table_name="application_documents")
    op.drop_table("application_documents")
    op.drop_index("ix_applications_workflow_current_state_id", table_name="applications")
    op.drop_index("ix_applications_workflow_application_id", table_name="applications")
    op.drop_index("ix_applications_applicant_subject", table_name="applications")
    op.drop_index("ix_applications_reference_number", table_name="applications")
    op.drop_table("applications")
