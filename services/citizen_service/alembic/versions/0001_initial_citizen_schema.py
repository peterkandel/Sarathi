"""initial citizen schema

Revision ID: 0001_initial_citizen_schema
Revises:
Create Date: 2026-06-20 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_citizen_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "citizen_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("identity_subject", sa.String(length=120), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=32), nullable=True),
        sa.Column("primary_language", sa.String(length=64), nullable=True),
        sa.Column("current_address", sa.String(length=500), nullable=True),
        sa.Column("permanent_address", sa.String(length=500), nullable=True),
        sa.Column("profile_status", sa.String(length=32), nullable=False),
        sa.Column("profile_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_subject", sa.String(length=120), nullable=True),
        sa.Column("updated_by_subject", sa.String(length=120), nullable=True),
        sa.UniqueConstraint("identity_subject", "deleted_at", name="uq_citizen_profiles_identity_subject_deleted_at"),
    )
    op.create_index("ix_citizen_profiles_identity_subject", "citizen_profiles", ["identity_subject"], unique=False)

    op.create_table(
        "citizenship_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("citizen_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("certificate_number", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column("issuing_office", sa.String(length=255), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("record_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_subject", sa.String(length=120), nullable=True),
        sa.Column("updated_by_subject", sa.String(length=120), nullable=True),
        sa.UniqueConstraint("certificate_number", "deleted_at", name="uq_citizenship_records_certificate_number_deleted_at"),
    )
    op.create_index("ix_citizenship_records_profile_id", "citizenship_records", ["profile_id"], unique=False)
    op.create_index("ix_citizenship_records_certificate_number", "citizenship_records", ["certificate_number"], unique=False)

    op.create_table(
        "document_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("citizen_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("document_status", sa.String(length=32), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by_subject", sa.String(length=120), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("document_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_subject", sa.String(length=120), nullable=True),
        sa.Column("updated_by_subject", sa.String(length=120), nullable=True),
        sa.UniqueConstraint("storage_key", "deleted_at", name="uq_document_metadata_storage_key_deleted_at"),
    )
    op.create_index("ix_document_metadata_profile_id", "document_metadata", ["profile_id"], unique=False)
    op.create_index("ix_document_metadata_document_type", "document_metadata", ["document_type"], unique=False)
    op.create_index("ix_document_metadata_storage_key", "document_metadata", ["storage_key"], unique=False)

    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("actor_subject", sa.String(length=120), nullable=True),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=True),
        sa.Column("resource_type", sa.String(length=120), nullable=True),
        sa.Column("resource_id", sa.String(length=120), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("correlation_id", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"], unique=False)
    op.create_index("ix_audit_events_actor_subject", "audit_events", ["actor_subject"], unique=False)
    op.create_index("ix_audit_events_aggregate_id", "audit_events", ["aggregate_id"], unique=False)
    op.create_index("ix_audit_events_correlation_id", "audit_events", ["correlation_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_events_correlation_id", table_name="audit_events")
    op.drop_index("ix_audit_events_aggregate_id", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_subject", table_name="audit_events")
    op.drop_index("ix_audit_events_event_type", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index("ix_document_metadata_storage_key", table_name="document_metadata")
    op.drop_index("ix_document_metadata_document_type", table_name="document_metadata")
    op.drop_index("ix_document_metadata_profile_id", table_name="document_metadata")
    op.drop_table("document_metadata")

    op.drop_index("ix_citizenship_records_certificate_number", table_name="citizenship_records")
    op.drop_index("ix_citizenship_records_profile_id", table_name="citizenship_records")
    op.drop_table("citizenship_records")

    op.drop_index("ix_citizen_profiles_identity_subject", table_name="citizen_profiles")
    op.drop_table("citizen_profiles")