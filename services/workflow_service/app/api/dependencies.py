from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import WorkflowService
from app.infrastructure.db import get_session
from app.infrastructure.repositories import (
    AuditRepository,
    WorkflowApplicationEventRepository,
    WorkflowApplicationRepository,
    WorkflowApprovalChainRepository,
    WorkflowApprovalStepRepository,
    WorkflowDefinitionRepository,
    WorkflowEscalationRuleRepository,
    WorkflowStateRepository,
    WorkflowTransitionRepository,
)


async def get_definition_repository(session: AsyncSession = Depends(get_session)) -> WorkflowDefinitionRepository:
    return WorkflowDefinitionRepository(session)


async def get_state_repository(session: AsyncSession = Depends(get_session)) -> WorkflowStateRepository:
    return WorkflowStateRepository(session)


async def get_transition_repository(session: AsyncSession = Depends(get_session)) -> WorkflowTransitionRepository:
    return WorkflowTransitionRepository(session)


async def get_approval_chain_repository(session: AsyncSession = Depends(get_session)) -> WorkflowApprovalChainRepository:
    return WorkflowApprovalChainRepository(session)


async def get_approval_step_repository(session: AsyncSession = Depends(get_session)) -> WorkflowApprovalStepRepository:
    return WorkflowApprovalStepRepository(session)


async def get_escalation_rule_repository(session: AsyncSession = Depends(get_session)) -> WorkflowEscalationRuleRepository:
    return WorkflowEscalationRuleRepository(session)


async def get_application_repository(session: AsyncSession = Depends(get_session)) -> WorkflowApplicationRepository:
    return WorkflowApplicationRepository(session)


async def get_application_event_repository(session: AsyncSession = Depends(get_session)) -> WorkflowApplicationEventRepository:
    return WorkflowApplicationEventRepository(session)


async def get_audit_repository(session: AsyncSession = Depends(get_session)) -> AuditRepository:
    return AuditRepository(session)


async def get_workflow_service(
    definition_repository: WorkflowDefinitionRepository = Depends(get_definition_repository),
    state_repository: WorkflowStateRepository = Depends(get_state_repository),
    transition_repository: WorkflowTransitionRepository = Depends(get_transition_repository),
    approval_chain_repository: WorkflowApprovalChainRepository = Depends(get_approval_chain_repository),
    approval_step_repository: WorkflowApprovalStepRepository = Depends(get_approval_step_repository),
    escalation_rule_repository: WorkflowEscalationRuleRepository = Depends(get_escalation_rule_repository),
    application_repository: WorkflowApplicationRepository = Depends(get_application_repository),
    application_event_repository: WorkflowApplicationEventRepository = Depends(get_application_event_repository),
    audit_repository: AuditRepository = Depends(get_audit_repository),
) -> WorkflowService:
    return WorkflowService(
        definition_repository,
        state_repository,
        transition_repository,
        approval_chain_repository,
        approval_step_repository,
        escalation_rule_repository,
        application_repository,
        application_event_repository,
        audit_repository,
    )
