"""initial ocr schema

Revision ID: 0001_initial_ocr_schema
Revises:
Create Date: 2026-06-21 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_ocr_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ocr_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("document_type_code", sa.String(length=120), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("original_storage_key", sa.String(length=255), nullable=False),
        sa.Column("normalized_storage_key", sa.String(length=255), nullable=True),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("pipeline_version", sa.String(length=32), nullable=False),
        sa.Column("document_confidence", sa.Float(), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("validation_status", sa.String(length=32), nullable=True),
        sa.Column("structured_output", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(length=32), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_subject", sa.String(length=120), nullable=True),
        sa.Column("updated_by_subject", sa.String(length=120), nullable=True),
        sa.UniqueConstraint("document_id", "file_id", "deleted_at", name="uq_ocr_jobs_document_file_deleted_at"),
    )
    op.create_index("ix_ocr_jobs_document_id", "ocr_jobs", ["document_id"], unique=False)
    op.create_index("ix_ocr_jobs_file_id", "ocr_jobs", ["file_id"], unique=False)
    op.create_index("ix_ocr_jobs_document_type_code", "ocr_jobs", ["document_type_code"], unique=False)

    op.create_table(
        "ocr_job_artifacts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("ocr_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("artifact_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("job_id", "storage_key", name="uq_ocr_job_artifacts_job_storage"),
    )
    op.create_index("ix_ocr_job_artifacts_job_id", "ocr_job_artifacts", ["job_id"], unique=False)
    op.create_index("ix_ocr_job_artifacts_stage", "ocr_job_artifacts", ["stage"], unique=False)

    op.create_table(
        "ocr_job_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("ocr_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ocr_job_events_job_id", "ocr_job_events", ["job_id"], unique=False)
    op.create_index("ix_ocr_job_events_event_type", "ocr_job_events", ["event_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ocr_job_events_event_type", table_name="ocr_job_events")
    op.drop_index("ix_ocr_job_events_job_id", table_name="ocr_job_events")
    op.drop_table("ocr_job_events")
    op.drop_index("ix_ocr_job_artifacts_stage", table_name="ocr_job_artifacts")
    op.drop_index("ix_ocr_job_artifacts_job_id", table_name="ocr_job_artifacts")
    op.drop_table("ocr_job_artifacts")
    op.drop_index("ix_ocr_jobs_document_type_code", table_name="ocr_jobs")
    op.drop_index("ix_ocr_jobs_file_id", table_name="ocr_jobs")
    op.drop_index("ix_ocr_jobs_document_id", table_name="ocr_jobs")
    op.drop_table("ocr_jobs")
