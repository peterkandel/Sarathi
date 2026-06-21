"""initial tax schema

Revision ID: 0001_initial_tax_schema
Revises:
Create Date: 2026-06-21 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_tax_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tax_rule_bundles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("rule_bundle_code", sa.String(length=120), nullable=False),
        sa.Column("rule_bundle_name", sa.String(length=255), nullable=False),
        sa.Column("jurisdiction_code", sa.String(length=120), nullable=False),
        sa.Column("tax_category_code", sa.String(length=120), nullable=False),
        sa.Column("taxpayer_class_code", sa.String(length=120), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("approval_reference", sa.String(length=255), nullable=True),
        sa.Column("rule_definition_hash", sa.String(length=128), nullable=False),
        sa.Column("bundle_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_actor_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_actor_id", sa.Uuid(), nullable=True),
        sa.UniqueConstraint("rule_bundle_code", "version_number", "deleted_at", name="uq_tax_rule_bundles_code_version_deleted_at"),
    )
    op.create_index("ix_tax_rule_bundles_rule_bundle_code", "tax_rule_bundles", ["rule_bundle_code"], unique=False)
    op.create_index("ix_tax_rule_bundles_jurisdiction_code", "tax_rule_bundles", ["jurisdiction_code"], unique=False)
    op.create_index("ix_tax_rule_bundles_tax_category_code", "tax_rule_bundles", ["tax_category_code"], unique=False)
    op.create_index("ix_tax_rule_bundles_taxpayer_class_code", "tax_rule_bundles", ["taxpayer_class_code"], unique=False)
    op.create_index("ix_tax_rule_bundles_effective_from", "tax_rule_bundles", ["effective_from"], unique=False)

    op.create_table(
        "tax_rule_components",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tax_rule_bundle_id", sa.Uuid(), sa.ForeignKey("tax_rule_bundles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("component_type", sa.String(length=64), nullable=False),
        sa.Column("component_code", sa.String(length=120), nullable=False),
        sa.Column("component_name", sa.String(length=255), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("applies_to", sa.JSON(), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_actor_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_actor_id", sa.Uuid(), nullable=True),
        sa.UniqueConstraint("tax_rule_bundle_id", "component_code", "deleted_at", name="uq_tax_rule_components_code_deleted_at"),
    )
    op.create_index("ix_tax_rule_components_tax_rule_bundle_id", "tax_rule_components", ["tax_rule_bundle_id"], unique=False)
    op.create_index("ix_tax_rule_components_component_type", "tax_rule_components", ["component_type"], unique=False)

    op.create_table(
        "tax_brackets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tax_rule_bundle_id", sa.Uuid(), sa.ForeignKey("tax_rule_bundles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bracket_order", sa.Integer(), nullable=False),
        sa.Column("lower_bound", sa.Float(), nullable=False),
        sa.Column("upper_bound", sa.Float(), nullable=True),
        sa.Column("marginal_rate", sa.Float(), nullable=False),
        sa.Column("base_tax", sa.Float(), nullable=False),
        sa.Column("bracket_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_actor_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_actor_id", sa.Uuid(), nullable=True),
        sa.UniqueConstraint("tax_rule_bundle_id", "bracket_order", "deleted_at", name="uq_tax_brackets_order_deleted_at"),
    )
    op.create_index("ix_tax_brackets_tax_rule_bundle_id", "tax_brackets", ["tax_rule_bundle_id"], unique=False)

    op.create_table(
        "tax_deductions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tax_rule_bundle_id", sa.Uuid(), sa.ForeignKey("tax_rule_bundles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("deduction_code", sa.String(length=120), nullable=False),
        sa.Column("deduction_name", sa.String(length=255), nullable=False),
        sa.Column("deduction_type", sa.String(length=64), nullable=False),
        sa.Column("calculation_basis", sa.String(length=120), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("priority_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_actor_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_actor_id", sa.Uuid(), nullable=True),
        sa.UniqueConstraint("tax_rule_bundle_id", "deduction_code", "deleted_at", name="uq_tax_deductions_code_deleted_at"),
    )
    op.create_index("ix_tax_deductions_tax_rule_bundle_id", "tax_deductions", ["tax_rule_bundle_id"], unique=False)
    op.create_index("ix_tax_deductions_deduction_code", "tax_deductions", ["deduction_code"], unique=False)

    op.create_table(
        "tax_exemptions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tax_rule_bundle_id", sa.Uuid(), sa.ForeignKey("tax_rule_bundles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exemption_code", sa.String(length=120), nullable=False),
        sa.Column("exemption_name", sa.String(length=255), nullable=False),
        sa.Column("exemption_type", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("percentage", sa.Float(), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("priority_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_actor_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_actor_id", sa.Uuid(), nullable=True),
        sa.UniqueConstraint("tax_rule_bundle_id", "exemption_code", "deleted_at", name="uq_tax_exemptions_code_deleted_at"),
    )
    op.create_index("ix_tax_exemptions_tax_rule_bundle_id", "tax_exemptions", ["tax_rule_bundle_id"], unique=False)
    op.create_index("ix_tax_exemptions_exemption_code", "tax_exemptions", ["exemption_code"], unique=False)

    op.create_table(
        "tax_calculations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tax_rule_bundle_id", sa.Uuid(), sa.ForeignKey("tax_rule_bundles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("taxpayer_subject", sa.String(length=120), nullable=False),
        sa.Column("jurisdiction_code", sa.String(length=120), nullable=False),
        sa.Column("tax_category_code", sa.String(length=120), nullable=False),
        sa.Column("taxpayer_class_code", sa.String(length=120), nullable=False),
        sa.Column("assessment_date", sa.Date(), nullable=False),
        sa.Column("gross_income", sa.Float(), nullable=False),
        sa.Column("taxable_income", sa.Float(), nullable=False),
        sa.Column("exemptions_total", sa.Float(), nullable=False),
        sa.Column("deductions_total", sa.Float(), nullable=False),
        sa.Column("tax_amount", sa.Float(), nullable=False),
        sa.Column("effective_tax_rate", sa.Float(), nullable=False),
        sa.Column("currency_code", sa.String(length=16), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tax_calculations_taxpayer_subject", "tax_calculations", ["taxpayer_subject"], unique=False)
    op.create_index("ix_tax_calculations_jurisdiction_code", "tax_calculations", ["jurisdiction_code"], unique=False)
    op.create_index("ix_tax_calculations_tax_category_code", "tax_calculations", ["tax_category_code"], unique=False)
    op.create_index("ix_tax_calculations_taxpayer_class_code", "tax_calculations", ["taxpayer_class_code"], unique=False)
    op.create_index("ix_tax_calculations_assessment_date", "tax_calculations", ["assessment_date"], unique=False)

    op.create_table(
        "tax_audit_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("actor_subject", sa.String(length=120), nullable=True),
        sa.Column("aggregate_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=True),
        sa.Column("resource_type", sa.String(length=120), nullable=True),
        sa.Column("resource_id", sa.String(length=120), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("correlation_id", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tax_audit_events_event_type", "tax_audit_events", ["event_type"], unique=False)
    op.create_index("ix_tax_audit_events_actor_subject", "tax_audit_events", ["actor_subject"], unique=False)
    op.create_index("ix_tax_audit_events_aggregate_id", "tax_audit_events", ["aggregate_id"], unique=False)
    op.create_index("ix_tax_audit_events_correlation_id", "tax_audit_events", ["correlation_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tax_audit_events_correlation_id", table_name="tax_audit_events")
    op.drop_index("ix_tax_audit_events_aggregate_id", table_name="tax_audit_events")
    op.drop_index("ix_tax_audit_events_actor_subject", table_name="tax_audit_events")
    op.drop_index("ix_tax_audit_events_event_type", table_name="tax_audit_events")
    op.drop_table("tax_audit_events")
    op.drop_index("ix_tax_calculations_assessment_date", table_name="tax_calculations")
    op.drop_index("ix_tax_calculations_taxpayer_class_code", table_name="tax_calculations")
    op.drop_index("ix_tax_calculations_tax_category_code", table_name="tax_calculations")
    op.drop_index("ix_tax_calculations_jurisdiction_code", table_name="tax_calculations")
    op.drop_index("ix_tax_calculations_taxpayer_subject", table_name="tax_calculations")
    op.drop_table("tax_calculations")
    op.drop_index("ix_tax_exemptions_exemption_code", table_name="tax_exemptions")
    op.drop_index("ix_tax_exemptions_tax_rule_bundle_id", table_name="tax_exemptions")
    op.drop_table("tax_exemptions")
    op.drop_index("ix_tax_deductions_deduction_code", table_name="tax_deductions")
    op.drop_index("ix_tax_deductions_tax_rule_bundle_id", table_name="tax_deductions")
    op.drop_table("tax_deductions")
    op.drop_index("ix_tax_brackets_tax_rule_bundle_id", table_name="tax_brackets")
    op.drop_table("tax_brackets")
    op.drop_index("ix_tax_rule_components_component_type", table_name="tax_rule_components")
    op.drop_index("ix_tax_rule_components_tax_rule_bundle_id", table_name="tax_rule_components")
    op.drop_table("tax_rule_components")
    op.drop_index("ix_tax_rule_bundles_effective_from", table_name="tax_rule_bundles")
    op.drop_index("ix_tax_rule_bundles_taxpayer_class_code", table_name="tax_rule_bundles")
    op.drop_index("ix_tax_rule_bundles_tax_category_code", table_name="tax_rule_bundles")
    op.drop_index("ix_tax_rule_bundles_jurisdiction_code", table_name="tax_rule_bundles")
    op.drop_index("ix_tax_rule_bundles_rule_bundle_code", table_name="tax_rule_bundles")
    op.drop_table("tax_rule_bundles")
