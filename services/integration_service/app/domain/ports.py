from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.domain.models import IntegrationAdapter, IntegrationAttempt, IntegrationCircuitBreaker, IntegrationEvent, IntegrationRequest


@dataclass(slots=True)
class AdapterExecutionResult:
    success: bool
    retryable: bool
    http_status: int | None = None
    external_reference: str | None = None
    response_payload: dict[str, object] | None = None
    error_code: str | None = None
    error_message: str | None = None


class IntegrationAdapterProtocol(Protocol):
    adapter_name: str
    system_code: str

    async def execute(self, request: IntegrationRequest, adapter: IntegrationAdapter, attempt_no: int) -> AdapterExecutionResult: ...


class IntegrationAdapterRepositoryProtocol(Protocol):
    async def create_adapter(self, adapter: IntegrationAdapter) -> IntegrationAdapter: ...
    async def get_adapter_by_id(self, adapter_id: UUID) -> IntegrationAdapter | None: ...
    async def get_adapter_by_code(self, adapter_code: str) -> IntegrationAdapter | None: ...
    async def list_adapters(self) -> Sequence[IntegrationAdapter]: ...


class IntegrationRequestRepositoryProtocol(Protocol):
    async def create_request(self, request: IntegrationRequest) -> IntegrationRequest: ...
    async def get_request_by_id(self, request_id: UUID) -> IntegrationRequest | None: ...
    async def list_due_requests(self, limit: int) -> Sequence[IntegrationRequest]: ...
    async def list_requests_for_adapter(self, adapter_id: UUID) -> Sequence[IntegrationRequest]: ...


class IntegrationAttemptRepositoryProtocol(Protocol):
    async def create_attempt(self, attempt: IntegrationAttempt) -> IntegrationAttempt: ...
    async def list_attempts_for_request(self, request_id: UUID) -> Sequence[IntegrationAttempt]: ...


class IntegrationCircuitBreakerRepositoryProtocol(Protocol):
    async def get_or_create_breaker(self, adapter: IntegrationAdapter) -> IntegrationCircuitBreaker: ...
    async def update_breaker(self, breaker: IntegrationCircuitBreaker) -> IntegrationCircuitBreaker: ...


class IntegrationEventRepositoryProtocol(Protocol):
    async def create_event(self, event: IntegrationEvent) -> IntegrationEvent: ...
    async def list_events_for_request(self, request_id: UUID) -> Sequence[IntegrationEvent]: ...
    async def list_pending_events(self, limit: int) -> Sequence[IntegrationEvent]: ...
