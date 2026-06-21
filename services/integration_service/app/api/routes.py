from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import get_integration_service
from app.application.services import IntegrationService
from app.domain.schemas import CircuitBreakerRead, IntegrationAdapterCreate, IntegrationAdapterRead, IntegrationAttemptRead, IntegrationEventRead, IntegrationRequestCreate, IntegrationRequestRead, MessageResponse, PublishResult, QueueProcessResult
from shared_auth import get_principal


router = APIRouter(tags=["integration"])


@router.post("/adapters", response_model=IntegrationAdapterRead, status_code=status.HTTP_201_CREATED)
async def create_adapter(request: Request, payload: IntegrationAdapterCreate, service: IntegrationService = Depends(get_integration_service)) -> IntegrationAdapterRead:
    adapter = await service.create_adapter(payload, get_principal(request))
    return IntegrationAdapterRead.model_validate(adapter, from_attributes=True)


@router.get("/adapters", response_model=list[IntegrationAdapterRead])
async def list_adapters(request: Request, service: IntegrationService = Depends(get_integration_service)) -> list[IntegrationAdapterRead]:
    adapters = await service.list_adapters(get_principal(request))
    return [IntegrationAdapterRead.model_validate(adapter, from_attributes=True) for adapter in adapters]


@router.get("/adapters/{adapter_id}", response_model=IntegrationAdapterRead)
async def get_adapter(adapter_id: UUID, request: Request, service: IntegrationService = Depends(get_integration_service)) -> IntegrationAdapterRead:
    adapter = await service.get_adapter(adapter_id, get_principal(request))
    return IntegrationAdapterRead.model_validate(adapter, from_attributes=True)


@router.post("/requests", response_model=IntegrationRequestRead, status_code=status.HTTP_201_CREATED)
async def create_request(request: Request, payload: IntegrationRequestCreate, service: IntegrationService = Depends(get_integration_service)) -> IntegrationRequestRead:
    return await service.submit_request(payload, get_principal(request))


@router.post("/requests/{request_id}/process", response_model=IntegrationRequestRead)
async def process_request(request_id: UUID, request: Request, service: IntegrationService = Depends(get_integration_service)) -> IntegrationRequestRead:
    return await service.process_request(request_id, get_principal(request))


@router.post("/queue/process", response_model=QueueProcessResult)
async def process_queue(request: Request, limit: int = 20, service: IntegrationService = Depends(get_integration_service)) -> QueueProcessResult:
    return await service.process_queue(limit, get_principal(request))


@router.get("/requests", response_model=list[IntegrationRequestRead])
async def list_requests(request: Request, adapter_id: UUID | None = None, service: IntegrationService = Depends(get_integration_service)) -> list[IntegrationRequestRead]:
    return await service.list_requests(get_principal(request), adapter_id=adapter_id)


@router.get("/requests/{request_id}", response_model=IntegrationRequestRead)
async def get_request(request_id: UUID, request: Request, service: IntegrationService = Depends(get_integration_service)) -> IntegrationRequestRead:
    return await service.get_request(request_id, get_principal(request))


@router.get("/requests/{request_id}/attempts", response_model=list[IntegrationAttemptRead])
async def list_attempts(request_id: UUID, request: Request, service: IntegrationService = Depends(get_integration_service)) -> list[IntegrationAttemptRead]:
    return await service.get_attempts(request_id, get_principal(request))


@router.get("/requests/{request_id}/events", response_model=list[IntegrationEventRead])
async def list_events(request_id: UUID, request: Request, service: IntegrationService = Depends(get_integration_service)) -> list[IntegrationEventRead]:
    return await service.get_events(request_id, get_principal(request))


@router.get("/breakers", response_model=list[CircuitBreakerRead])
async def list_breakers(request: Request, service: IntegrationService = Depends(get_integration_service)) -> list[CircuitBreakerRead]:
    return await service.list_breakers(get_principal(request))


@router.post("/events/publish", response_model=PublishResult)
async def publish_events(request: Request, limit: int = 20, service: IntegrationService = Depends(get_integration_service)) -> PublishResult:
    return await service.publish_events(limit, get_principal(request))


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "integration_service"}
