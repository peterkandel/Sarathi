from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import IntegrationEventPayload
from app.domain.models import CircuitBreakerState, IntegrationAdapter, IntegrationAttempt, IntegrationCircuitBreaker, IntegrationEvent, IntegrationEventPublicationStatus, IntegrationRequest, IntegrationRequestStatus


class IntegrationAdapterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_adapter(self, adapter: IntegrationAdapter) -> IntegrationAdapter:
        self.session.add(adapter)
        await self.session.flush()
        return adapter

    async def get_adapter_by_id(self, adapter_id: UUID) -> IntegrationAdapter | None:
        result = await self.session.execute(select(IntegrationAdapter).where(IntegrationAdapter.id == adapter_id, IntegrationAdapter.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def get_adapter_by_code(self, adapter_code: str) -> IntegrationAdapter | None:
        result = await self.session.execute(select(IntegrationAdapter).where(IntegrationAdapter.adapter_code == adapter_code, IntegrationAdapter.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def list_adapters(self) -> Sequence[IntegrationAdapter]:
        result = await self.session.execute(select(IntegrationAdapter).where(IntegrationAdapter.deleted_at.is_(None)).order_by(IntegrationAdapter.created_at.desc()))
        return list(result.scalars().all())


class IntegrationRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_request(self, request: IntegrationRequest) -> IntegrationRequest:
        self.session.add(request)
        await self.session.flush()
        return request

    async def get_request_by_id(self, request_id: UUID) -> IntegrationRequest | None:
        result = await self.session.execute(select(IntegrationRequest).where(IntegrationRequest.id == request_id, IntegrationRequest.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def list_due_requests(self, limit: int) -> Sequence[IntegrationRequest]:
        now = datetime.utcnow()
        result = await self.session.execute(
            select(IntegrationRequest)
            .where(
                IntegrationRequest.deleted_at.is_(None),
                IntegrationRequest.status.in_([IntegrationRequestStatus.QUEUED.value, IntegrationRequestStatus.RETRYING.value]),
                (IntegrationRequest.next_retry_at.is_(None)) | (IntegrationRequest.next_retry_at <= now),
            )
            .order_by(IntegrationRequest.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_requests_for_adapter(self, adapter_id: UUID) -> Sequence[IntegrationRequest]:
        result = await self.session.execute(select(IntegrationRequest).where(IntegrationRequest.adapter_id == adapter_id, IntegrationRequest.deleted_at.is_(None)).order_by(IntegrationRequest.created_at.desc()))
        return list(result.scalars().all())


class IntegrationAttemptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_attempt(self, attempt: IntegrationAttempt) -> IntegrationAttempt:
        self.session.add(attempt)
        await self.session.flush()
        return attempt

    async def list_attempts_for_request(self, request_id: UUID) -> Sequence[IntegrationAttempt]:
        result = await self.session.execute(select(IntegrationAttempt).where(IntegrationAttempt.request_id == request_id, IntegrationAttempt.deleted_at.is_(None)).order_by(IntegrationAttempt.attempt_no.asc()))
        return list(result.scalars().all())


class IntegrationCircuitBreakerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_breaker(self, adapter: IntegrationAdapter) -> IntegrationCircuitBreaker:
        result = await self.session.execute(select(IntegrationCircuitBreaker).where(IntegrationCircuitBreaker.adapter_id == adapter.id))
        breaker = result.scalar_one_or_none()
        if breaker is not None:
            return breaker
        breaker = IntegrationCircuitBreaker(adapter_id=adapter.id, reset_after_seconds=adapter.breaker_reset_seconds)
        self.session.add(breaker)
        await self.session.flush()
        return breaker

    async def update_breaker(self, breaker: IntegrationCircuitBreaker) -> IntegrationCircuitBreaker:
        self.session.add(breaker)
        await self.session.flush()
        return breaker


class IntegrationEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_event(self, event: IntegrationEventPayload) -> IntegrationEvent:
        integration_event = IntegrationEvent(
            request_id=event.request_id,
            event_type=event.event_type,
            old_status=event.old_status,
            new_status=event.new_status,
            publication_status=event.publication_status,
            payload=event.payload,
            channel=event.channel,
        )
        self.session.add(integration_event)
        await self.session.flush()
        return integration_event

    async def list_events_for_request(self, request_id: UUID) -> Sequence[IntegrationEvent]:
        result = await self.session.execute(select(IntegrationEvent).where(IntegrationEvent.request_id == request_id, IntegrationEvent.deleted_at.is_(None)).order_by(IntegrationEvent.created_at.asc()))
        return list(result.scalars().all())

    async def list_pending_events(self, limit: int) -> Sequence[IntegrationEvent]:
        result = await self.session.execute(select(IntegrationEvent).where(IntegrationEvent.publication_status == IntegrationEventPublicationStatus.PENDING.value, IntegrationEvent.deleted_at.is_(None)).order_by(IntegrationEvent.created_at.asc()).limit(limit))
        return list(result.scalars().all())
