from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import IntegrationService
from app.infrastructure.db import get_session
from app.infrastructure.repositories import IntegrationAdapterRepository, IntegrationAttemptRepository, IntegrationCircuitBreakerRepository, IntegrationEventRepository, IntegrationRequestRepository


async def get_adapter_repository(session: AsyncSession = Depends(get_session)) -> IntegrationAdapterRepository:
    return IntegrationAdapterRepository(session)


async def get_request_repository(session: AsyncSession = Depends(get_session)) -> IntegrationRequestRepository:
    return IntegrationRequestRepository(session)


async def get_attempt_repository(session: AsyncSession = Depends(get_session)) -> IntegrationAttemptRepository:
    return IntegrationAttemptRepository(session)


async def get_breaker_repository(session: AsyncSession = Depends(get_session)) -> IntegrationCircuitBreakerRepository:
    return IntegrationCircuitBreakerRepository(session)


async def get_event_repository(session: AsyncSession = Depends(get_session)) -> IntegrationEventRepository:
    return IntegrationEventRepository(session)


async def get_integration_service(
    adapter_repository: IntegrationAdapterRepository = Depends(get_adapter_repository),
    request_repository: IntegrationRequestRepository = Depends(get_request_repository),
    attempt_repository: IntegrationAttemptRepository = Depends(get_attempt_repository),
    breaker_repository: IntegrationCircuitBreakerRepository = Depends(get_breaker_repository),
    event_repository: IntegrationEventRepository = Depends(get_event_repository),
) -> IntegrationService:
    return IntegrationService(adapter_repository, request_repository, attempt_repository, breaker_repository, event_repository)
