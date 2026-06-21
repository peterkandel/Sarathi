from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import AuditEvent
from app.domain.models import (
    AuditEvent as AuditEventModel,
    WorkflowApplication,
    WorkflowApplicationEvent,
    WorkflowApprovalChain,
    WorkflowApprovalStep,
    WorkflowDefinition,
    WorkflowEscalationRule,
    WorkflowState,
    WorkflowTransition,
)


class WorkflowDefinitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_definition(self, definition: WorkflowDefinition) -> WorkflowDefinition:
        self.session.add(definition)
        await self.session.flush()
        return definition

    async def update_definition(self, definition: WorkflowDefinition) -> WorkflowDefinition:
        self.session.add(definition)
        await self.session.flush()
        return definition

    async def get_definition_by_id(self, definition_id: UUID) -> WorkflowDefinition | None:
        result = await self.session.execute(select(WorkflowDefinition).where(WorkflowDefinition.id == definition_id, WorkflowDefinition.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def get_definition_by_code_version(self, code: str, version: str) -> WorkflowDefinition | None:
        result = await self.session.execute(select(WorkflowDefinition).where(WorkflowDefinition.code == code, WorkflowDefinition.version == version, WorkflowDefinition.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def list_definitions(self) -> Sequence[WorkflowDefinition]:
        result = await self.session.execute(select(WorkflowDefinition).where(WorkflowDefinition.deleted_at.is_(None)).order_by(WorkflowDefinition.created_at.desc()))
        return list(result.scalars().all())


class WorkflowStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_state(self, state: WorkflowState) -> WorkflowState:
        self.session.add(state)
        await self.session.flush()
        return state

    async def update_state(self, state: WorkflowState) -> WorkflowState:
        self.session.add(state)
        await self.session.flush()
        return state

    async def get_state_by_id(self, state_id: UUID) -> WorkflowState | None:
        result = await self.session.execute(select(WorkflowState).where(WorkflowState.id == state_id, WorkflowState.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def list_states_for_definition(self, definition_id: UUID) -> Sequence[WorkflowState]:
        result = await self.session.execute(select(WorkflowState).where(WorkflowState.definition_id == definition_id, WorkflowState.deleted_at.is_(None)).order_by(WorkflowState.sort_order.asc()))
        return list(result.scalars().all())


class WorkflowTransitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_transition(self, transition: WorkflowTransition) -> WorkflowTransition:
        self.session.add(transition)
        await self.session.flush()
        return transition

    async def get_transition_by_id(self, transition_id: UUID) -> WorkflowTransition | None:
        result = await self.session.execute(select(WorkflowTransition).where(WorkflowTransition.id == transition_id, WorkflowTransition.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def get_transition(self, definition_id: UUID, from_state_id: UUID, action: str) -> WorkflowTransition | None:
        result = await self.session.execute(select(WorkflowTransition).where(WorkflowTransition.definition_id == definition_id, WorkflowTransition.from_state_id == from_state_id, WorkflowTransition.action == action, WorkflowTransition.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def list_transitions_for_definition(self, definition_id: UUID) -> Sequence[WorkflowTransition]:
        result = await self.session.execute(select(WorkflowTransition).where(WorkflowTransition.definition_id == definition_id, WorkflowTransition.deleted_at.is_(None)))
        return list(result.scalars().all())


class WorkflowApprovalChainRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_chain(self, chain: WorkflowApprovalChain) -> WorkflowApprovalChain:
        self.session.add(chain)
        await self.session.flush()
        return chain

    async def get_chain_by_id(self, chain_id: UUID) -> WorkflowApprovalChain | None:
        result = await self.session.execute(select(WorkflowApprovalChain).where(WorkflowApprovalChain.id == chain_id, WorkflowApprovalChain.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def get_active_chain_for_state(self, definition_id: UUID, source_state_id: UUID) -> WorkflowApprovalChain | None:
        result = await self.session.execute(select(WorkflowApprovalChain).where(WorkflowApprovalChain.definition_id == definition_id, WorkflowApprovalChain.source_state_id == source_state_id, WorkflowApprovalChain.is_active.is_(True), WorkflowApprovalChain.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def list_chains_for_definition(self, definition_id: UUID) -> Sequence[WorkflowApprovalChain]:
        result = await self.session.execute(select(WorkflowApprovalChain).where(WorkflowApprovalChain.definition_id == definition_id, WorkflowApprovalChain.deleted_at.is_(None)))
        return list(result.scalars().all())


class WorkflowApprovalStepRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_step(self, step: WorkflowApprovalStep) -> WorkflowApprovalStep:
        self.session.add(step)
        await self.session.flush()
        return step

    async def list_steps_for_chain(self, chain_id: UUID) -> Sequence[WorkflowApprovalStep]:
        result = await self.session.execute(select(WorkflowApprovalStep).where(WorkflowApprovalStep.chain_id == chain_id).order_by(WorkflowApprovalStep.step_order.asc()))
        return list(result.scalars().all())


class WorkflowEscalationRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_rule(self, rule: WorkflowEscalationRule) -> WorkflowEscalationRule:
        self.session.add(rule)
        await self.session.flush()
        return rule

    async def get_active_rule_for_state(self, definition_id: UUID, source_state_id: UUID) -> WorkflowEscalationRule | None:
        result = await self.session.execute(select(WorkflowEscalationRule).where(WorkflowEscalationRule.definition_id == definition_id, WorkflowEscalationRule.source_state_id == source_state_id, WorkflowEscalationRule.is_active.is_(True), WorkflowEscalationRule.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def list_rules_for_definition(self, definition_id: UUID) -> Sequence[WorkflowEscalationRule]:
        result = await self.session.execute(select(WorkflowEscalationRule).where(WorkflowEscalationRule.definition_id == definition_id, WorkflowEscalationRule.deleted_at.is_(None)))
        return list(result.scalars().all())


class WorkflowApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_application(self, application: WorkflowApplication) -> WorkflowApplication:
        self.session.add(application)
        await self.session.flush()
        return application

    async def update_application(self, application: WorkflowApplication) -> WorkflowApplication:
        self.session.add(application)
        await self.session.flush()
        return application

    async def get_application_by_id(self, application_id: UUID) -> WorkflowApplication | None:
        result = await self.session.execute(select(WorkflowApplication).where(WorkflowApplication.id == application_id, WorkflowApplication.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def list_applications(self) -> Sequence[WorkflowApplication]:
        result = await self.session.execute(select(WorkflowApplication).where(WorkflowApplication.deleted_at.is_(None)).order_by(WorkflowApplication.created_at.desc()))
        return list(result.scalars().all())

    async def list_applications_for_subject(self, applicant_subject: str) -> Sequence[WorkflowApplication]:
        result = await self.session.execute(select(WorkflowApplication).where(WorkflowApplication.applicant_subject == applicant_subject, WorkflowApplication.deleted_at.is_(None)).order_by(WorkflowApplication.created_at.desc()))
        return list(result.scalars().all())


class WorkflowApplicationEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_event(self, event: WorkflowApplicationEvent) -> WorkflowApplicationEvent:
        self.session.add(event)
        await self.session.flush()
        return event


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(self, event: AuditEvent) -> AuditEvent:
        event_model = AuditEventModel(
            event_type=event.event_type,
            actor_subject=event.actor_subject,
            aggregate_id=event.aggregate_id,
            action=event.action,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            outcome=event.outcome,
            payload=event.payload,
            details=event.details,
        )
        self.session.add(event_model)
        await self.session.flush()
        return event
