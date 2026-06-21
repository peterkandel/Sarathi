"""initial workflow schema

Revision ID: 0001_initial_workflow_schema
Revises:
Create Date: 2026-06-21 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_workflow_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("definition_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_subject", sa.String(length=120), nullable=True),
        sa.Column("updated_by_subject", sa.String(length=120), nullable=True),
        sa.UniqueConstraint("code", "version", "deleted_at", name="uq_workflow_definitions_code_version_deleted_at"),
    )
    op.create_index("ix_workflow_definitions_code", "workflow_definitions", ["code"], unique=False)
    op.create_index("ix_workflow_definitions_version", "workflow_definitions", ["version"], unique=False)

    op.create_table(
        "workflow_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("state_kind", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_initial", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_terminal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("state_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_subject", sa.String(length=120), nullable=True),
        sa.Column("updated_by_subject", sa.String(length=120), nullable=True),
        sa.UniqueConstraint("definition_id", "code", "deleted_at", name="uq_workflow_states_definition_code_deleted_at"),
    )
    op.create_index("ix_workflow_states_definition_id", "workflow_states", ["definition_id"], unique=False)
    op.create_index("ix_workflow_states_code", "workflow_states", ["code"], unique=False)

    op.create_table(
        "workflow_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_state_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_state_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("allowed_roles", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("requires_approval_chain", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("transition_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_subject", sa.String(length=120), nullable=True),
        sa.Column("updated_by_subject", sa.String(length=120), nullable=True),
        sa.UniqueConstraint("definition_id", "from_state_id", "action", "deleted_at", name="uq_workflow_transitions_definition_from_action_deleted_at"),
    )
    op.create_index("ix_workflow_transitions_definition_id", "workflow_transitions", ["definition_id"], unique=False)
    op.create_index("ix_workflow_transitions_from_state_id", "workflow_transitions", ["from_state_id"], unique=False)
    op.create_index("ix_workflow_transitions_to_state_id", "workflow_transitions", ["to_state_id"], unique=False)

    op.create_table(
        "workflow_approval_chains",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_state_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("chain_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_subject", sa.String(length=120), nullable=True),
        sa.Column("updated_by_subject", sa.String(length=120), nullable=True),
    )
    op.create_index("ix_workflow_approval_chains_definition_id", "workflow_approval_chains", ["definition_id"], unique=False)
    op.create_index("ix_workflow_approval_chains_source_state_id", "workflow_approval_chains", ["source_state_id"], unique=False)

    op.create_table(
        "workflow_approval_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("chain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_approval_chains.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("required_role", sa.String(length=120), nullable=False),
        sa.Column("step_name", sa.String(length=255), nullable=False),
        sa.Column("step_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_subject", sa.String(length=120), nullable=True),
        sa.Column("updated_by_subject", sa.String(length=120), nullable=True),
        sa.UniqueConstraint("chain_id", "step_order", name="uq_workflow_approval_steps_chain_step_order"),
    )
    op.create_index("ix_workflow_approval_steps_chain_id", "workflow_approval_steps", ["chain_id"], unique=False)

    op.create_table(
        "workflow_escalation_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_state_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_state_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False),
        sa.Column("after_minutes", sa.Integer(), nullable=False),
        sa.Column("escalation_action", sa.String(length=120), nullable=False, server_default=sa.text("'escalate'")),
        sa.Column("target_role", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("escalation_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_subject", sa.String(length=120), nullable=True),
        sa.Column("updated_by_subject", sa.String(length=120), nullable=True),
    )
    op.create_index("ix_workflow_escalation_rules_definition_id", "workflow_escalation_rules", ["definition_id"], unique=False)
    op.create_index("ix_workflow_escalation_rules_source_state_id", "workflow_escalation_rules", ["source_state_id"], unique=False)

    op.create_table(
        "workflow_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("applicant_subject", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("current_state_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("approval_chain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_approval_chains.id", ondelete="SET NULL"), nullable=True),
        sa.Column("current_step_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalation_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("application_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_subject", sa.String(length=120), nullable=True),
        sa.Column("updated_by_subject", sa.String(length=120), nullable=True),
        sa.UniqueConstraint("definition_id", "entity_type", "entity_id", "deleted_at", name="uq_workflow_applications_definition_entity_deleted_at"),
    )
    op.create_index("ix_workflow_applications_definition_id", "workflow_applications", ["definition_id"], unique=False)
    op.create_index("ix_workflow_applications_applicant_subject", "workflow_applications", ["applicant_subject"], unique=False)
    op.create_index("ix_workflow_applications_entity_type", "workflow_applications", ["entity_type"], unique=False)
    op.create_index("ix_workflow_applications_entity_id", "workflow_applications", ["entity_id"], unique=False)
    op.create_index("ix_workflow_applications_current_state_id", "workflow_applications", ["current_state_id"], unique=False)

    op.create_table(
        "workflow_application_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("from_state_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_states.id", ondelete="SET NULL"), nullable=True),
        sa.Column("to_state_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_states.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_subject", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_workflow_application_events_application_id", "workflow_application_events", ["application_id"], unique=False)
    op.create_index("ix_workflow_application_events_event_type", "workflow_application_events", ["event_type"], unique=False)
    op.create_index("ix_workflow_application_events_actor_subject", "workflow_application_events", ["actor_subject"], unique=False)

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

    op.drop_index("ix_workflow_application_events_actor_subject", table_name="workflow_application_events")
    op.drop_index("ix_workflow_application_events_event_type", table_name="workflow_application_events")
    op.drop_index("ix_workflow_application_events_application_id", table_name="workflow_application_events")
    op.drop_table("workflow_application_events")

    op.drop_index("ix_workflow_applications_current_state_id", table_name="workflow_applications")
    op.drop_index("ix_workflow_applications_entity_id", table_name="workflow_applications")
    op.drop_index("ix_workflow_applications_entity_type", table_name="workflow_applications")
    op.drop_index("ix_workflow_applications_applicant_subject", table_name="workflow_applications")
    op.drop_index("ix_workflow_applications_definition_id", table_name="workflow_applications")
    op.drop_table("workflow_applications")

    op.drop_index("ix_workflow_escalation_rules_source_state_id", table_name="workflow_escalation_rules")
    op.drop_index("ix_workflow_escalation_rules_definition_id", table_name="workflow_escalation_rules")
    op.drop_table("workflow_escalation_rules")

    op.drop_index("ix_workflow_approval_steps_chain_id", table_name="workflow_approval_steps")
    op.drop_table("workflow_approval_steps")

    op.drop_index("ix_workflow_approval_chains_source_state_id", table_name="workflow_approval_chains")
    op.drop_index("ix_workflow_approval_chains_definition_id", table_name="workflow_approval_chains")
    op.drop_table("workflow_approval_chains")

    op.drop_index("ix_workflow_transitions_to_state_id", table_name="workflow_transitions")
    op.drop_index("ix_workflow_transitions_from_state_id", table_name="workflow_transitions")
    op.drop_index("ix_workflow_transitions_definition_id", table_name="workflow_transitions")
    op.drop_table("workflow_transitions")

    op.drop_index("ix_workflow_states_code", table_name="workflow_states")
    op.drop_index("ix_workflow_states_definition_id", table_name="workflow_states")
    op.drop_table("workflow_states")

    op.drop_index("ix_workflow_definitions_version", table_name="workflow_definitions")
    op.drop_index("ix_workflow_definitions_code", table_name="workflow_definitions")
    op.drop_table("workflow_definitions")
