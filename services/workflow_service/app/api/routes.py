from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import get_workflow_service
from app.application.services import WorkflowService
from app.domain.schemas import (
    MessageResponse,
    WorkflowApprovalChainCreate,
    WorkflowApprovalChainRead,
    WorkflowApprovalStepCreate,
    WorkflowApprovalStepRead,
    WorkflowApplicationAction,
    WorkflowApplicationRead,
    WorkflowApplicationSubmission,
    WorkflowDefinitionCreate,
    WorkflowDefinitionRead,
    WorkflowDefinitionUpdate,
    WorkflowEscalationRuleCreate,
    WorkflowEscalationRuleRead,
    WorkflowStateCreate,
    WorkflowStateRead,
    WorkflowStateUpdate,
    WorkflowTransitionCreate,
    WorkflowTransitionRead,
)
from shared_auth import get_principal


router = APIRouter(tags=["workflow"])


@router.post("/definitions", response_model=WorkflowDefinitionRead, status_code=status.HTTP_201_CREATED)
async def create_definition(request: Request, payload: WorkflowDefinitionCreate, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowDefinitionRead:
    definition = await service.create_definition(payload, get_principal(request))
    return WorkflowDefinitionRead.model_validate(definition, from_attributes=True)


@router.get("/definitions", response_model=list[WorkflowDefinitionRead])
async def list_definitions(request: Request, service: WorkflowService = Depends(get_workflow_service)) -> list[WorkflowDefinitionRead]:
    definitions = await service.list_definitions(get_principal(request))
    return [WorkflowDefinitionRead.model_validate(definition, from_attributes=True) for definition in definitions]


@router.get("/definitions/{definition_id}", response_model=WorkflowDefinitionRead)
async def get_definition(definition_id: UUID, request: Request, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowDefinitionRead:
    definition = await service.get_definition(definition_id)
    return WorkflowDefinitionRead.model_validate(definition, from_attributes=True)


@router.patch("/definitions/{definition_id}", response_model=WorkflowDefinitionRead)
async def update_definition(definition_id: UUID, request: Request, payload: WorkflowDefinitionUpdate, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowDefinitionRead:
    definition = await service.update_definition(definition_id, payload, get_principal(request))
    return WorkflowDefinitionRead.model_validate(definition, from_attributes=True)


@router.post("/definitions/{definition_id}/states", response_model=WorkflowStateRead, status_code=status.HTTP_201_CREATED)
async def create_state(definition_id: UUID, request: Request, payload: WorkflowStateCreate, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowStateRead:
    state = await service.create_state(definition_id, payload, get_principal(request))
    return WorkflowStateRead.model_validate(state, from_attributes=True)


@router.get("/definitions/{definition_id}/states", response_model=list[WorkflowStateRead])
async def list_states(definition_id: UUID, request: Request, service: WorkflowService = Depends(get_workflow_service)) -> list[WorkflowStateRead]:
    states = await service.list_states(definition_id, get_principal(request))
    return [WorkflowStateRead.model_validate(state, from_attributes=True) for state in states]


@router.patch("/states/{state_id}", response_model=WorkflowStateRead)
async def update_state(state_id: UUID, request: Request, payload: WorkflowStateUpdate, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowStateRead:
    state = await service.update_state(state_id, payload, get_principal(request))
    return WorkflowStateRead.model_validate(state, from_attributes=True)


@router.post("/definitions/{definition_id}/transitions", response_model=WorkflowTransitionRead, status_code=status.HTTP_201_CREATED)
async def create_transition(definition_id: UUID, request: Request, payload: WorkflowTransitionCreate, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowTransitionRead:
    transition = await service.create_transition(definition_id, payload, get_principal(request))
    return WorkflowTransitionRead.model_validate(transition, from_attributes=True)


@router.get("/definitions/{definition_id}/transitions", response_model=list[WorkflowTransitionRead])
async def list_transitions(definition_id: UUID, request: Request, service: WorkflowService = Depends(get_workflow_service)) -> list[WorkflowTransitionRead]:
    transitions = await service.list_transitions(definition_id, get_principal(request))
    return [WorkflowTransitionRead.model_validate(transition, from_attributes=True) for transition in transitions]


@router.post("/definitions/{definition_id}/approval-chains", response_model=WorkflowApprovalChainRead, status_code=status.HTTP_201_CREATED)
async def create_approval_chain(definition_id: UUID, request: Request, payload: WorkflowApprovalChainCreate, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowApprovalChainRead:
    chain = await service.create_approval_chain(definition_id, payload, get_principal(request))
    return WorkflowApprovalChainRead.model_validate(chain, from_attributes=True)


@router.post("/approval-chains/{chain_id}/steps", response_model=WorkflowApprovalStepRead, status_code=status.HTTP_201_CREATED)
async def add_approval_step(chain_id: UUID, request: Request, payload: WorkflowApprovalStepCreate, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowApprovalStepRead:
    step = await service.add_approval_step(chain_id, payload, get_principal(request))
    return WorkflowApprovalStepRead.model_validate(step, from_attributes=True)


@router.get("/definitions/{definition_id}/approval-chains", response_model=list[WorkflowApprovalChainRead])
async def list_chains(definition_id: UUID, request: Request, service: WorkflowService = Depends(get_workflow_service)) -> list[WorkflowApprovalChainRead]:
    chains = await service.list_chains(definition_id, get_principal(request))
    return [WorkflowApprovalChainRead.model_validate(chain, from_attributes=True) for chain in chains]


@router.post("/definitions/{definition_id}/escalation-rules", response_model=WorkflowEscalationRuleRead, status_code=status.HTTP_201_CREATED)
async def create_escalation_rule(definition_id: UUID, request: Request, payload: WorkflowEscalationRuleCreate, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowEscalationRuleRead:
    rule = await service.add_escalation_rule(definition_id, payload, get_principal(request))
    return WorkflowEscalationRuleRead.model_validate(rule, from_attributes=True)


@router.get("/definitions/{definition_id}/escalation-rules", response_model=list[WorkflowEscalationRuleRead])
async def list_escalation_rules(definition_id: UUID, request: Request, service: WorkflowService = Depends(get_workflow_service)) -> list[WorkflowEscalationRuleRead]:
    rules = await service.list_escalation_rules(definition_id, get_principal(request))
    return [WorkflowEscalationRuleRead.model_validate(rule, from_attributes=True) for rule in rules]


@router.post("/applications/submit", response_model=WorkflowApplicationRead, status_code=status.HTTP_201_CREATED)
async def submit_application(request: Request, payload: WorkflowApplicationSubmission, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowApplicationRead:
    application = await service.submit_application(payload, get_principal(request))
    return WorkflowApplicationRead.model_validate(application, from_attributes=True)


@router.get("/applications", response_model=list[WorkflowApplicationRead])
async def list_applications(request: Request, service: WorkflowService = Depends(get_workflow_service)) -> list[WorkflowApplicationRead]:
    applications = await service.list_applications(get_principal(request))
    return [WorkflowApplicationRead.model_validate(application, from_attributes=True) for application in applications]


@router.get("/applications/{application_id}", response_model=WorkflowApplicationRead)
async def get_application(application_id: UUID, request: Request, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowApplicationRead:
    application = await service.get_application(application_id, get_principal(request))
    return WorkflowApplicationRead.model_validate(application, from_attributes=True)


@router.post("/applications/{application_id}/transition", response_model=WorkflowApplicationRead)
async def transition_application(application_id: UUID, action: str, request: Request, payload: WorkflowApplicationAction, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowApplicationRead:
    application = await service.transition_application(application_id, action, payload, get_principal(request))
    return WorkflowApplicationRead.model_validate(application, from_attributes=True)


@router.post("/applications/{application_id}/approve", response_model=WorkflowApplicationRead)
async def approve_application(application_id: UUID, request: Request, payload: WorkflowApplicationAction, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowApplicationRead:
    application = await service.approve_application(application_id, payload, get_principal(request))
    return WorkflowApplicationRead.model_validate(application, from_attributes=True)


@router.post("/applications/{application_id}/reject", response_model=WorkflowApplicationRead)
async def reject_application(application_id: UUID, request: Request, payload: WorkflowApplicationAction, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowApplicationRead:
    application = await service.reject_application(application_id, payload, get_principal(request))
    return WorkflowApplicationRead.model_validate(application, from_attributes=True)


@router.post("/applications/{application_id}/escalate", response_model=WorkflowApplicationRead)
async def escalate_application(application_id: UUID, request: Request, payload: WorkflowApplicationAction, service: WorkflowService = Depends(get_workflow_service)) -> WorkflowApplicationRead:
    application = await service.escalate_application(application_id, payload, get_principal(request))
    return WorkflowApplicationRead.model_validate(application, from_attributes=True)


@router.post("/applications/evaluations/escalations", response_model=list[WorkflowApplicationRead])
async def evaluate_escalations(request: Request, service: WorkflowService = Depends(get_workflow_service)) -> list[WorkflowApplicationRead]:
    applications = await service.evaluate_escalations(get_principal(request))
    return [WorkflowApplicationRead.model_validate(application, from_attributes=True) for application in applications]


@router.get("/applications/{application_id}/events", response_model=list[WorkflowApplicationRead])
async def application_events(application_id: UUID, request: Request, service: WorkflowService = Depends(get_workflow_service)) -> list[WorkflowApplicationRead]:
    application = await service.get_application(application_id, get_principal(request))
    return [WorkflowApplicationRead.model_validate(application, from_attributes=True)]


@router.delete("/definitions/{definition_id}", response_model=MessageResponse)
async def delete_definition(definition_id: UUID, request: Request, service: WorkflowService = Depends(get_workflow_service)) -> MessageResponse:
    await service.update_definition(definition_id, WorkflowDefinitionUpdate(is_active=False), get_principal(request))
    return MessageResponse(message="Workflow definition deactivated")
