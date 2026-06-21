from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Table, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditMixin:
    created_by_subject: Mapped[str | None] = mapped_column(String(120), nullable=True)
    updated_by_subject: Mapped[str | None] = mapped_column(String(120), nullable=True)


class WorkflowDefinition(Base, TimestampMixin, AuditMixin):
    __tablename__ = "workflow_definitions"
    __table_args__ = (UniqueConstraint("code", "version", "deleted_at", name="uq_workflow_definitions_code_version_deleted_at"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    definition_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    states: Mapped[list[WorkflowState]] = relationship("WorkflowState", back_populates="definition", cascade="all, delete-orphan")
    transitions: Mapped[list[WorkflowTransition]] = relationship("WorkflowTransition", back_populates="definition", cascade="all, delete-orphan")
    approval_chains: Mapped[list[WorkflowApprovalChain]] = relationship("WorkflowApprovalChain", back_populates="definition", cascade="all, delete-orphan")
    escalation_rules: Mapped[list[WorkflowEscalationRule]] = relationship("WorkflowEscalationRule", back_populates="definition", cascade="all, delete-orphan")
    applications: Mapped[list[WorkflowApplication]] = relationship("WorkflowApplication", back_populates="definition", cascade="all, delete-orphan")


class WorkflowState(Base, TimestampMixin, AuditMixin):
    __tablename__ = "workflow_states"
    __table_args__ = (UniqueConstraint("definition_id", "code", "deleted_at", name="uq_workflow_states_definition_code_deleted_at"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    definition_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state_kind: Mapped[str] = mapped_column(String(64), nullable=False, default="NORMAL")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_initial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    state_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    definition: Mapped[WorkflowDefinition] = relationship("WorkflowDefinition", back_populates="states")
    outgoing_transitions: Mapped[list[WorkflowTransition]] = relationship("WorkflowTransition", foreign_keys="WorkflowTransition.from_state_id", back_populates="from_state", cascade="all, delete-orphan")
    incoming_transitions: Mapped[list[WorkflowTransition]] = relationship("WorkflowTransition", foreign_keys="WorkflowTransition.to_state_id", back_populates="to_state")
    approval_chains: Mapped[list[WorkflowApprovalChain]] = relationship("WorkflowApprovalChain", back_populates="source_state", foreign_keys="WorkflowApprovalChain.source_state_id")
    escalation_rules: Mapped[list[WorkflowEscalationRule]] = relationship("WorkflowEscalationRule", back_populates="source_state", foreign_keys="WorkflowEscalationRule.source_state_id")


class WorkflowTransition(Base, TimestampMixin, AuditMixin):
    __tablename__ = "workflow_transitions"
    __table_args__ = (UniqueConstraint("definition_id", "from_state_id", "action", "deleted_at", name="uq_workflow_transitions_definition_from_action_deleted_at"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    definition_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    from_state_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False, index=True)
    to_state_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    allowed_roles: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    requires_approval_chain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    transition_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    definition: Mapped[WorkflowDefinition] = relationship("WorkflowDefinition", back_populates="transitions")
    from_state: Mapped[WorkflowState] = relationship("WorkflowState", foreign_keys=[from_state_id], back_populates="outgoing_transitions")
    to_state: Mapped[WorkflowState] = relationship("WorkflowState", foreign_keys=[to_state_id], back_populates="incoming_transitions")


class WorkflowApprovalChain(Base, TimestampMixin, AuditMixin):
    __tablename__ = "workflow_approval_chains"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    definition_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    source_state_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    chain_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    definition: Mapped[WorkflowDefinition] = relationship("WorkflowDefinition", back_populates="approval_chains")
    source_state: Mapped[WorkflowState] = relationship("WorkflowState", back_populates="approval_chains", foreign_keys=[source_state_id])
    steps: Mapped[list[WorkflowApprovalStep]] = relationship("WorkflowApprovalStep", back_populates="chain", cascade="all, delete-orphan", order_by="WorkflowApprovalStep.step_order")


class WorkflowApprovalStep(Base, TimestampMixin, AuditMixin):
    __tablename__ = "workflow_approval_steps"
    __table_args__ = (UniqueConstraint("chain_id", "step_order", name="uq_workflow_approval_steps_chain_step_order"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    chain_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_approval_chains.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    required_role: Mapped[str] = mapped_column(String(120), nullable=False)
    step_name: Mapped[str] = mapped_column(String(255), nullable=False)
    step_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    chain: Mapped[WorkflowApprovalChain] = relationship("WorkflowApprovalChain", back_populates="steps")


class WorkflowEscalationRule(Base, TimestampMixin, AuditMixin):
    __tablename__ = "workflow_escalation_rules"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    definition_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    source_state_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False, index=True)
    target_state_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False, index=True)
    after_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    escalation_action: Mapped[str] = mapped_column(String(120), nullable=False, default="escalate")
    target_role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    escalation_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    definition: Mapped[WorkflowDefinition] = relationship("WorkflowDefinition", back_populates="escalation_rules")
    source_state: Mapped[WorkflowState] = relationship("WorkflowState", back_populates="escalation_rules", foreign_keys=[source_state_id])
    target_state: Mapped[WorkflowState] = relationship("WorkflowState", foreign_keys=[target_state_id])


class WorkflowApplication(Base, TimestampMixin, AuditMixin):
    __tablename__ = "workflow_applications"
    __table_args__ = (UniqueConstraint("definition_id", "entity_type", "entity_id", "deleted_at", name="uq_workflow_applications_definition_entity_deleted_at"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    definition_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    applicant_subject: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    current_state_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    approval_chain_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_approval_chains.id", ondelete="SET NULL"), nullable=True, index=True)
    current_step_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    escalation_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    application_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    definition: Mapped[WorkflowDefinition] = relationship("WorkflowDefinition", back_populates="applications")
    current_state: Mapped[WorkflowState] = relationship("WorkflowState", foreign_keys=[current_state_id])
    approval_chain: Mapped[WorkflowApprovalChain | None] = relationship("WorkflowApprovalChain", foreign_keys=[approval_chain_id])
    events: Mapped[list[WorkflowApplicationEvent]] = relationship("WorkflowApplicationEvent", back_populates="application", cascade="all, delete-orphan")


class WorkflowApplicationEvent(Base, TimestampMixin):
    __tablename__ = "workflow_application_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    from_state_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_states.id", ondelete="SET NULL"), nullable=True)
    to_state_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflow_states.id", ondelete="SET NULL"), nullable=True)
    actor_subject: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    application: Mapped[WorkflowApplication] = relationship("WorkflowApplication", back_populates="events")


class AuditEvent(Base, TimestampMixin):
    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    actor_subject: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    aggregate_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    action: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    details: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    correlation_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
