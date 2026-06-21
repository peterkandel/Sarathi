from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status

from app.domain.events import AuditEvent
from app.domain.models import (
    WorkflowApplication,
    WorkflowApplicationEvent,
    WorkflowApprovalChain,
    WorkflowApprovalStep,
    WorkflowDefinition,
    WorkflowEscalationRule,
    WorkflowState,
    WorkflowTransition,
)
from app.domain.schemas import (
    WorkflowApprovalChainCreate,
    WorkflowApprovalStepCreate,
    WorkflowApplicationAction,
    WorkflowApplicationSubmission,
    WorkflowDefinitionCreate,
    WorkflowDefinitionUpdate,
    WorkflowEscalationRuleCreate,
    WorkflowStateCreate,
    WorkflowStateUpdate,
    WorkflowTransitionCreate,
)
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
from shared_auth import Role
from shared_auth.models import Principal
from shared_auth.security import has_any_role


ADMIN_ROLES = (Role.MANAGER, Role.ADMINISTRATOR, Role.SUPER_ADMINISTRATOR)
APPROVAL_ROLES = (Role.CLERK, Role.REVIEWER, Role.MANAGER, Role.ADMINISTRATOR, Role.SUPER_ADMINISTRATOR)


class WorkflowService:
    def __init__(
        self,
        definition_repository: WorkflowDefinitionRepository,
        state_repository: WorkflowStateRepository,
        transition_repository: WorkflowTransitionRepository,
        approval_chain_repository: WorkflowApprovalChainRepository,
        approval_step_repository: WorkflowApprovalStepRepository,
        escalation_rule_repository: WorkflowEscalationRuleRepository,
        application_repository: WorkflowApplicationRepository,
        application_event_repository: WorkflowApplicationEventRepository,
        audit_repository: AuditRepository,
    ) -> None:
        self.definitions = definition_repository
        self.states = state_repository
        self.transitions = transition_repository
        self.chains = approval_chain_repository
        self.steps = approval_step_repository
        self.rules = escalation_rule_repository
        self.applications = application_repository
        self.application_events = application_event_repository
        self.audit = audit_repository

    def _require_admin(self, principal: Principal) -> None:
        if not has_any_role(principal, ADMIN_ROLES):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrative role required")

    def _require_approval_role(self, principal: Principal) -> None:
        if not has_any_role(principal, APPROVAL_ROLES):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Approval role required")

    def _has_role(self, principal: Principal, role_name: str) -> bool:
        return any(role.value == role_name for role in principal.roles)

    def _as_utc(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    async def create_definition(self, payload: WorkflowDefinitionCreate, principal: Principal) -> WorkflowDefinition:
        self._require_admin(principal)
        existing = await self.definitions.get_definition_by_code_version(payload.code, payload.version)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Workflow definition already exists")
        definition = WorkflowDefinition(
            code=payload.code,
            name=payload.name,
            version=payload.version,
            description=payload.description,
            is_active=payload.is_active,
            definition_metadata=payload.definition_metadata,
            created_by_subject=principal.subject,
            updated_by_subject=principal.subject,
        )
        created = await self.definitions.create_definition(definition)
        await self.audit.record_event(AuditEvent(event_type="WorkflowDefinitionCreated", actor_subject=principal.subject, aggregate_id=created.id, action="create_definition", resource_type="workflow_definition", resource_id=str(created.id), outcome="success", payload={"code": created.code, "version": created.version}))
        return created

    async def update_definition(self, definition_id: UUID, payload: WorkflowDefinitionUpdate, principal: Principal) -> WorkflowDefinition:
        self._require_admin(principal)
        definition = await self.get_definition(definition_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field_name, field_value in update_data.items():
            setattr(definition, field_name, field_value)
        definition.updated_by_subject = principal.subject
        updated = await self.definitions.update_definition(definition)
        await self.audit.record_event(AuditEvent(event_type="WorkflowDefinitionUpdated", actor_subject=principal.subject, aggregate_id=updated.id, action="update_definition", resource_type="workflow_definition", resource_id=str(updated.id), outcome="success", payload=update_data))
        return updated

    async def get_definition(self, definition_id: UUID) -> WorkflowDefinition:
        definition = await self.definitions.get_definition_by_id(definition_id)
        if definition is None or definition.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow definition not found")
        return definition

    async def get_definition_by_code_version(self, code: str, version: str) -> WorkflowDefinition:
        definition = await self.definitions.get_definition_by_code_version(code, version)
        if definition is None or definition.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow definition not found")
        return definition

    async def list_definitions(self, principal: Principal) -> list[WorkflowDefinition]:
        self._require_admin(principal)
        return list(await self.definitions.list_definitions())

    async def create_state(self, definition_id: UUID, payload: WorkflowStateCreate, principal: Principal) -> WorkflowState:
        self._require_admin(principal)
        definition = await self.get_definition(definition_id)
        for state in await self.states.list_states_for_definition(definition.id):
            if state.code == payload.code and state.deleted_at is None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Workflow state already exists")
        state = WorkflowState(
            definition_id=definition.id,
            code=payload.code,
            name=payload.name,
            state_kind=payload.state_kind,
            sort_order=payload.sort_order,
            is_initial=payload.is_initial,
            is_terminal=payload.is_terminal,
            state_metadata=payload.state_metadata,
            created_by_subject=principal.subject,
            updated_by_subject=principal.subject,
        )
        created = await self.states.create_state(state)
        await self.audit.record_event(AuditEvent(event_type="WorkflowStateCreated", actor_subject=principal.subject, aggregate_id=created.id, action="create_state", resource_type="workflow_state", resource_id=str(created.id), outcome="success", payload={"definition_id": str(definition.id), "code": created.code}))
        return created

    async def update_state(self, state_id: UUID, payload: WorkflowStateUpdate, principal: Principal) -> WorkflowState:
        self._require_admin(principal)
        state = await self.get_state(state_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field_name, field_value in update_data.items():
            setattr(state, field_name, field_value)
        state.updated_by_subject = principal.subject
        updated = await self.states.update_state(state)
        await self.audit.record_event(AuditEvent(event_type="WorkflowStateUpdated", actor_subject=principal.subject, aggregate_id=updated.id, action="update_state", resource_type="workflow_state", resource_id=str(updated.id), outcome="success", payload=update_data))
        return updated

    async def get_state(self, state_id: UUID) -> WorkflowState:
        state = await self.states.get_state_by_id(state_id)
        if state is None or state.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow state not found")
        return state

    async def list_states(self, definition_id: UUID, principal: Principal) -> list[WorkflowState]:
        self._require_admin(principal)
        return list(await self.states.list_states_for_definition(definition_id))

    async def create_transition(self, definition_id: UUID, payload: WorkflowTransitionCreate, principal: Principal) -> WorkflowTransition:
        self._require_admin(principal)
        definition = await self.get_definition(definition_id)
        from_state = await self.get_state(payload.from_state_id)
        to_state = await self.get_state(payload.to_state_id)
        if from_state.definition_id != definition.id or to_state.definition_id != definition.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transition states must belong to the definition")
        transition = WorkflowTransition(
            definition_id=definition.id,
            from_state_id=from_state.id,
            to_state_id=to_state.id,
            action=payload.action,
            allowed_roles=payload.allowed_roles,
            requires_approval_chain=payload.requires_approval_chain,
            transition_metadata=payload.transition_metadata,
            created_by_subject=principal.subject,
            updated_by_subject=principal.subject,
        )
        created = await self.transitions.create_transition(transition)
        await self.audit.record_event(AuditEvent(event_type="WorkflowTransitionCreated", actor_subject=principal.subject, aggregate_id=created.id, action="create_transition", resource_type="workflow_transition", resource_id=str(created.id), outcome="success", payload={"definition_id": str(definition.id), "action": created.action}))
        return created

    async def list_transitions(self, definition_id: UUID, principal: Principal) -> list[WorkflowTransition]:
        self._require_admin(principal)
        return list(await self.transitions.list_transitions_for_definition(definition_id))

    async def create_approval_chain(self, definition_id: UUID, payload: WorkflowApprovalChainCreate, principal: Principal) -> WorkflowApprovalChain:
        self._require_admin(principal)
        definition = await self.get_definition(definition_id)
        source_state = await self.get_state(payload.source_state_id)
        if source_state.definition_id != definition.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Approval chain state must belong to the definition")
        chain = WorkflowApprovalChain(
            definition_id=definition.id,
            source_state_id=source_state.id,
            name=payload.name,
            is_active=payload.is_active,
            chain_metadata=payload.chain_metadata,
            created_by_subject=principal.subject,
            updated_by_subject=principal.subject,
        )
        created = await self.chains.create_chain(chain)
        await self.audit.record_event(AuditEvent(event_type="WorkflowApprovalChainCreated", actor_subject=principal.subject, aggregate_id=created.id, action="create_chain", resource_type="workflow_approval_chain", resource_id=str(created.id), outcome="success", payload={"definition_id": str(definition.id), "source_state_id": str(source_state.id)}))
        return created

    async def add_approval_step(self, chain_id: UUID, payload: WorkflowApprovalStepCreate, principal: Principal) -> WorkflowApprovalStep:
        self._require_admin(principal)
        chain = await self.get_chain(chain_id)
        step = WorkflowApprovalStep(
            chain_id=chain.id,
            step_order=payload.step_order,
            required_role=payload.required_role,
            step_name=payload.step_name,
            step_metadata=payload.step_metadata,
            created_by_subject=principal.subject,
            updated_by_subject=principal.subject,
        )
        created = await self.steps.create_step(step)
        await self.audit.record_event(AuditEvent(event_type="WorkflowApprovalStepCreated", actor_subject=principal.subject, aggregate_id=created.id, action="create_approval_step", resource_type="workflow_approval_step", resource_id=str(created.id), outcome="success", payload={"chain_id": str(chain.id), "step_order": created.step_order}))
        return created

    async def get_chain(self, chain_id: UUID) -> WorkflowApprovalChain:
        chain = await self.chains.get_chain_by_id(chain_id)
        if chain is None or chain.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval chain not found")
        return chain

    async def list_chains(self, definition_id: UUID, principal: Principal) -> list[WorkflowApprovalChain]:
        self._require_admin(principal)
        return list(await self.chains.list_chains_for_definition(definition_id))

    async def add_escalation_rule(self, definition_id: UUID, payload: WorkflowEscalationRuleCreate, principal: Principal) -> WorkflowEscalationRule:
        self._require_admin(principal)
        definition = await self.get_definition(definition_id)
        source_state = await self.get_state(payload.source_state_id)
        target_state = await self.get_state(payload.target_state_id)
        if source_state.definition_id != definition.id or target_state.definition_id != definition.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Escalation states must belong to the definition")
        rule = WorkflowEscalationRule(
            definition_id=definition.id,
            source_state_id=source_state.id,
            target_state_id=target_state.id,
            after_minutes=payload.after_minutes,
            escalation_action=payload.escalation_action,
            target_role=payload.target_role,
            is_active=payload.is_active,
            escalation_metadata=payload.escalation_metadata,
            created_by_subject=principal.subject,
            updated_by_subject=principal.subject,
        )
        created = await self.rules.create_rule(rule)
        await self.audit.record_event(AuditEvent(event_type="WorkflowEscalationRuleCreated", actor_subject=principal.subject, aggregate_id=created.id, action="create_escalation_rule", resource_type="workflow_escalation_rule", resource_id=str(created.id), outcome="success", payload={"definition_id": str(definition.id), "source_state_id": str(source_state.id)}))
        return created

    async def list_escalation_rules(self, definition_id: UUID, principal: Principal) -> list[WorkflowEscalationRule]:
        self._require_admin(principal)
        return list(await self.rules.list_rules_for_definition(definition_id))

    async def submit_application(self, payload: WorkflowApplicationSubmission, principal: Principal) -> WorkflowApplication:
        definition = await self.get_definition_by_code_version(payload.definition_code, payload.definition_version)
        if not definition.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow definition is not active")
        initial_state = next((state for state in await self.states.list_states_for_definition(definition.id) if state.is_initial and state.deleted_at is None), None)
        if initial_state is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow definition has no initial state")
        chain = await self.chains.get_active_chain_for_state(definition.id, initial_state.id)
        escalation_rule = await self.rules.get_active_rule_for_state(definition.id, initial_state.id)
        now = datetime.now(timezone.utc)
        application = WorkflowApplication(
            definition_id=definition.id,
            applicant_subject=principal.subject,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            title=payload.title,
            payload=payload.payload,
            current_state_id=initial_state.id,
            status="ACTIVE",
            approval_chain_id=chain.id if chain else None,
            current_step_order=1 if chain else 0,
            submitted_at=now,
            escalation_due_at=now + timedelta(minutes=escalation_rule.after_minutes) if escalation_rule else None,
            application_metadata=payload.application_metadata,
            created_by_subject=principal.subject,
            updated_by_subject=principal.subject,
        )
        created = await self.applications.create_application(application)
        await self.application_events.create_event(WorkflowApplicationEvent(application_id=created.id, event_type="ApplicationSubmitted", from_state_id=None, to_state_id=initial_state.id, actor_subject=principal.subject, notes=None, payload={"entity_type": payload.entity_type, "entity_id": payload.entity_id}))
        await self.audit.record_event(AuditEvent(event_type="WorkflowApplicationSubmitted", actor_subject=principal.subject, aggregate_id=created.id, action="submit_application", resource_type="workflow_application", resource_id=str(created.id), outcome="success", payload={"definition_code": definition.code, "definition_version": definition.version}))
        return created

    async def list_applications(self, principal: Principal) -> list[WorkflowApplication]:
        if has_any_role(principal, ADMIN_ROLES):
            return list(await self.applications.list_applications())
        return list(await self.applications.list_applications_for_subject(principal.subject))

    async def get_application(self, application_id: UUID, principal: Principal) -> WorkflowApplication:
        application = await self.applications.get_application_by_id(application_id)
        if application is None or application.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow application not found")
        if application.applicant_subject != principal.subject and not has_any_role(principal, ADMIN_ROLES + APPROVAL_ROLES):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Application access denied")
        return application

    async def transition_application(self, application_id: UUID, action: str, payload: WorkflowApplicationAction, principal: Principal) -> WorkflowApplication:
        application = await self.get_application(application_id, principal)
        return await self._apply_transition(application, action, payload, principal)

    async def approve_application(self, application_id: UUID, payload: WorkflowApplicationAction, principal: Principal) -> WorkflowApplication:
        self._require_approval_role(principal)
        application = await self.get_application(application_id, principal)
        if application.approval_chain_id is not None:
            chain = await self.get_chain(application.approval_chain_id)
            steps = await self.steps.list_steps_for_chain(chain.id)
            if not steps:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Approval chain has no steps")
            current_index = max(application.current_step_order, 1)
            current_step = next((step for step in steps if step.step_order == current_index), None)
            if current_step is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Approval chain is complete")
            if not self._has_role(principal, current_step.required_role):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Approval role not permitted")
            event_notes = payload.notes or f"Approved step {current_step.step_order}"
            if current_step.step_order < len(steps):
                application.current_step_order = current_step.step_order + 1
                application.updated_by_subject = principal.subject
                updated = await self.applications.update_application(application)
                await self.application_events.create_event(WorkflowApplicationEvent(application_id=updated.id, event_type="ApprovalStepCompleted", from_state_id=updated.current_state_id, to_state_id=updated.current_state_id, actor_subject=principal.subject, notes=event_notes, payload={"step_order": current_step.step_order}))
                await self.audit.record_event(AuditEvent(event_type="WorkflowApprovalStepCompleted", actor_subject=principal.subject, aggregate_id=updated.id, action="approve_step", resource_type="workflow_application", resource_id=str(updated.id), outcome="success", payload={"step_order": current_step.step_order}))
                return updated
        return await self._apply_transition(application, "approve", payload, principal)

    async def reject_application(self, application_id: UUID, payload: WorkflowApplicationAction, principal: Principal) -> WorkflowApplication:
        self._require_approval_role(principal)
        application = await self.get_application(application_id, principal)
        return await self._apply_transition(application, "reject", payload, principal)

    async def escalate_application(self, application_id: UUID, payload: WorkflowApplicationAction, principal: Principal) -> WorkflowApplication:
        self._require_admin(principal)
        application = await self.get_application(application_id, principal)
        rule = await self.rules.get_active_rule_for_state(application.definition_id, application.current_state_id)
        if rule is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No escalation rule for current state")
        escalation_due_at = self._as_utc(application.escalation_due_at)
        if escalation_due_at is not None and escalation_due_at > datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application is not yet eligible for escalation")
        return await self._apply_transition(application, rule.escalation_action, payload, principal, forced_target_state_id=rule.target_state_id)

    async def _apply_transition(
        self,
        application: WorkflowApplication,
        action: str,
        payload: WorkflowApplicationAction,
        principal: Principal,
        *,
        forced_target_state_id: UUID | None = None,
    ) -> WorkflowApplication:
        current_state = await self.get_state(application.current_state_id)
        transition = await self.transitions.get_transition(application.definition_id, current_state.id, action)
        if transition is None and forced_target_state_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transition not allowed")
        if transition is not None and transition.allowed_roles:
            allowed_roles = [role_name for role_name in transition.allowed_roles if role_name in {role.value for role in Role}]
            if allowed_roles and not any(self._has_role(principal, role_name) for role_name in allowed_roles):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not permitted for transition")
        target_state_id = forced_target_state_id or (transition.to_state_id if transition else None)
        if target_state_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transition target missing")
        target_state = await self.get_state(target_state_id)
        from_state_id = application.current_state_id
        application.current_state_id = target_state.id
        application.updated_by_subject = principal.subject
        if target_state.is_terminal:
            application.status = "COMPLETED"
            application.resolved_at = datetime.now(timezone.utc)
            application.approval_chain_id = None
            application.current_step_order = 0
        if action == "escalate":
            application.escalated_at = datetime.now(timezone.utc)
        if target_state.id != from_state_id:
            escalation_rule = await self.rules.get_active_rule_for_state(application.definition_id, target_state.id)
            application.escalation_due_at = datetime.now(timezone.utc) + timedelta(minutes=escalation_rule.after_minutes) if escalation_rule else None
            chain = await self.chains.get_active_chain_for_state(application.definition_id, target_state.id)
            if chain is not None:
                application.approval_chain_id = chain.id
                application.current_step_order = 1
            else:
                application.approval_chain_id = None
                application.current_step_order = 0
        updated = await self.applications.update_application(application)
        await self.application_events.create_event(WorkflowApplicationEvent(application_id=updated.id, event_type=f"Application{action.title()}", from_state_id=from_state_id, to_state_id=target_state.id, actor_subject=principal.subject, notes=payload.notes, payload=payload.payload))
        await self.audit.record_event(AuditEvent(event_type="WorkflowApplicationTransitioned", actor_subject=principal.subject, aggregate_id=updated.id, action=action, resource_type="workflow_application", resource_id=str(updated.id), outcome="success", payload={"from_state_id": str(from_state_id), "to_state_id": str(target_state.id)}))
        return updated

    async def evaluate_escalations(self, principal: Principal) -> list[WorkflowApplication]:
        self._require_admin(principal)
        now = datetime.now(timezone.utc)
        updated_applications: list[WorkflowApplication] = []
        for application in await self.applications.list_applications():
            rule = await self.rules.get_active_rule_for_state(application.definition_id, application.current_state_id)
            escalation_due_at = self._as_utc(application.escalation_due_at)
            if rule is None or escalation_due_at is None or escalation_due_at > now:
                continue
            escalated = await self._apply_transition(application, rule.escalation_action, WorkflowApplicationAction(notes="Auto-escalated"), principal, forced_target_state_id=rule.target_state_id)
            updated_applications.append(escalated)
        return updated_applications
