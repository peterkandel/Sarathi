from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkflowDefinitionBase(BaseModel):
    code: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=255)
    version: str = Field(min_length=1, max_length=32)
    description: str | None = None
    is_active: bool = True
    definition_metadata: dict[str, object] = Field(default_factory=dict)


class WorkflowDefinitionCreate(WorkflowDefinitionBase):
    pass


class WorkflowDefinitionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None
    definition_metadata: dict[str, object] | None = None


class WorkflowDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    version: str
    description: str | None
    is_active: bool
    definition_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class WorkflowStateBase(BaseModel):
    code: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=255)
    state_kind: str = Field(default="NORMAL", max_length=64)
    sort_order: int = 0
    is_initial: bool = False
    is_terminal: bool = False
    state_metadata: dict[str, object] = Field(default_factory=dict)


class WorkflowStateCreate(WorkflowStateBase):
    pass


class WorkflowStateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    state_kind: str | None = Field(default=None, max_length=64)
    sort_order: int | None = None
    is_initial: bool | None = None
    is_terminal: bool | None = None
    state_metadata: dict[str, object] | None = None


class WorkflowStateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    definition_id: UUID
    code: str
    name: str
    state_kind: str
    sort_order: int
    is_initial: bool
    is_terminal: bool
    state_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class WorkflowTransitionBase(BaseModel):
    from_state_id: UUID
    to_state_id: UUID
    action: str = Field(min_length=1, max_length=120)
    allowed_roles: list[str] = Field(default_factory=list)
    requires_approval_chain: bool = False
    transition_metadata: dict[str, object] = Field(default_factory=dict)


class WorkflowTransitionCreate(WorkflowTransitionBase):
    pass


class WorkflowTransitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    definition_id: UUID
    from_state_id: UUID
    to_state_id: UUID
    action: str
    allowed_roles: list[str]
    requires_approval_chain: bool
    transition_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class WorkflowApprovalChainBase(BaseModel):
    source_state_id: UUID
    name: str = Field(min_length=1, max_length=255)
    is_active: bool = True
    chain_metadata: dict[str, object] = Field(default_factory=dict)


class WorkflowApprovalChainCreate(WorkflowApprovalChainBase):
    pass


class WorkflowApprovalChainRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    definition_id: UUID
    source_state_id: UUID
    name: str
    is_active: bool
    chain_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class WorkflowApprovalStepBase(BaseModel):
    step_order: int = Field(ge=1)
    required_role: str = Field(min_length=1, max_length=120)
    step_name: str = Field(min_length=1, max_length=255)
    step_metadata: dict[str, object] = Field(default_factory=dict)


class WorkflowApprovalStepCreate(WorkflowApprovalStepBase):
    pass


class WorkflowApprovalStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chain_id: UUID
    step_order: int
    required_role: str
    step_name: str
    step_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class WorkflowEscalationRuleBase(BaseModel):
    source_state_id: UUID
    target_state_id: UUID
    after_minutes: int = Field(ge=0)
    escalation_action: str = Field(default="escalate", max_length=120)
    target_role: str | None = Field(default=None, max_length=120)
    is_active: bool = True
    escalation_metadata: dict[str, object] = Field(default_factory=dict)


class WorkflowEscalationRuleCreate(WorkflowEscalationRuleBase):
    pass


class WorkflowEscalationRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    definition_id: UUID
    source_state_id: UUID
    target_state_id: UUID
    after_minutes: int
    escalation_action: str
    target_role: str | None
    is_active: bool
    escalation_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class WorkflowApplicationSubmission(BaseModel):
    definition_code: str = Field(min_length=1, max_length=120)
    definition_version: str = Field(min_length=1, max_length=32)
    entity_type: str = Field(min_length=1, max_length=120)
    entity_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=255)
    payload: dict[str, object] = Field(default_factory=dict)
    application_metadata: dict[str, object] = Field(default_factory=dict)


class WorkflowApplicationAction(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)
    payload: dict[str, object] = Field(default_factory=dict)


class WorkflowApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    definition_id: UUID
    applicant_subject: str
    entity_type: str
    entity_id: str
    title: str
    payload: dict[str, object]
    current_state_id: UUID
    status: str
    approval_chain_id: UUID | None
    current_step_order: int
    submitted_at: datetime
    resolved_at: datetime | None
    escalated_at: datetime | None
    escalation_due_at: datetime | None
    application_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str
