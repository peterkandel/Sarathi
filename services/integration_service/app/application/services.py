from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status

from app.domain.events import CircuitBreakerSnapshot, IntegrationEventPayload, IntegrationErrorPayload
from app.domain.models import CircuitBreakerState, IntegrationAdapter, IntegrationAttempt, IntegrationAttemptStatus, IntegrationCircuitBreaker, IntegrationEvent, IntegrationEventPublicationStatus, IntegrationRequest, IntegrationRequestStatus
from app.domain.ports import AdapterExecutionResult, IntegrationAdapterRepositoryProtocol, IntegrationAttemptRepositoryProtocol, IntegrationCircuitBreakerRepositoryProtocol, IntegrationEventRepositoryProtocol, IntegrationRequestRepositoryProtocol
from app.domain.schemas import CircuitBreakerRead, IntegrationAdapterCreate, IntegrationAdapterRead, IntegrationAttemptRead, IntegrationEventRead, IntegrationRequestCreate, IntegrationRequestRead, MessageResponse, PublishResult, QueueProcessResult
from app.infrastructure.adapters import adapter_registry
from shared_auth import Role
from shared_auth.models import Principal
from shared_auth.security import has_any_role


ADMIN_ROLES = (Role.ADMINISTRATOR, Role.SUPER_ADMINISTRATOR)


class IntegrationServiceError(HTTPException):
    def __init__(self, status_code: int, error_code: str, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(status_code=status_code, detail={"error_code": error_code, "message": message, "details": details or {}})
        self.error_code = error_code
        self.message = message
        self.details = details or {}


class IntegrationService:
    def __init__(
        self,
        adapters: IntegrationAdapterRepositoryProtocol,
        requests: IntegrationRequestRepositoryProtocol,
        attempts: IntegrationAttemptRepositoryProtocol,
        breakers: IntegrationCircuitBreakerRepositoryProtocol,
        events: IntegrationEventRepositoryProtocol,
    ) -> None:
        self.adapters = adapters
        self.requests = requests
        self.attempts = attempts
        self.breakers = breakers
        self.events = events

    def _is_admin(self, principal: Principal) -> bool:
        return has_any_role(principal, ADMIN_ROLES)

    def _require_admin(self, principal: Principal) -> None:
        if not self._is_admin(principal):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrative role required")

    def _now(self) -> datetime:
        return datetime.utcnow()

    def _backoff_seconds(self, attempt_no: int) -> int:
        return min(300, 2 ** max(0, attempt_no - 1))

    async def create_adapter(self, payload: IntegrationAdapterCreate, principal: Principal) -> IntegrationAdapter:
        self._require_admin(principal)
        adapter = IntegrationAdapter(
            adapter_code=payload.adapter_code,
            adapter_name=payload.adapter_name,
            system_code=payload.system_code,
            adapter_type=payload.adapter_type,
            base_url=payload.base_url,
            auth_type=payload.auth_type,
            timeout_seconds=payload.timeout_seconds,
            max_retry_attempts=payload.max_retry_attempts,
            breaker_failure_threshold=payload.breaker_failure_threshold,
            breaker_reset_seconds=payload.breaker_reset_seconds,
            enabled=payload.enabled,
            adapter_metadata=payload.adapter_metadata,
        )
        created = await self.adapters.create_adapter(adapter)
        await self.breakers.get_or_create_breaker(created)
        return created

    async def list_adapters(self, principal: Principal) -> list[IntegrationAdapter]:
        self._require_admin(principal)
        return list(await self.adapters.list_adapters())

    async def get_adapter(self, adapter_id: UUID, principal: Principal) -> IntegrationAdapter:
        self._require_admin(principal)
        adapter = await self.adapters.get_adapter_by_id(adapter_id)
        if adapter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration adapter not found")
        return adapter

    async def submit_request(self, payload: IntegrationRequestCreate, principal: Principal) -> IntegrationRequestRead:
        adapter = await self.adapters.get_adapter_by_code(payload.adapter_code)
        if adapter is None or not adapter.enabled:
            raise IntegrationServiceError(status.HTTP_404_NOT_FOUND, "INT-4001", "Integration adapter not found or disabled", {"adapter_code": payload.adapter_code})
        await self.breakers.get_or_create_breaker(adapter)

        request = IntegrationRequest(
            adapter_id=adapter.id,
            system_code=adapter.system_code,
            operation_code=payload.operation_code,
            idempotency_key=payload.idempotency_key,
            correlation_id=payload.correlation_id,
            external_reference=payload.external_reference,
            canonical_payload=payload.canonical_payload,
            request_payload=payload.request_payload,
            status=IntegrationRequestStatus.QUEUED.value,
            retry_count=0,
            max_attempts=payload.max_attempts or adapter.max_retry_attempts,
            next_retry_at=self._now(),
        )
        created = await self.requests.create_request(request)
        await self.events.create_event(IntegrationEventPayload(request_id=created.id, event_type="IntegrationRequested", new_status=created.status, payload={"adapter_code": adapter.adapter_code, "system_code": adapter.system_code, "operation_code": created.operation_code}))
        return IntegrationRequestRead.model_validate(created, from_attributes=True)

    async def process_request(self, request_id: UUID, principal: Principal) -> IntegrationRequestRead:
        request = await self.requests.get_request_by_id(request_id)
        if request is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration request not found")
        adapter = await self.adapters.get_adapter_by_id(request.adapter_id)
        if adapter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration adapter not found")
        breaker = await self.breakers.get_or_create_breaker(adapter)
        return await self._execute_request(request, adapter, breaker, principal)

    async def process_queue(self, limit: int, principal: Principal) -> QueueProcessResult:
        self._require_admin(principal)
        due_requests = await self.requests.list_due_requests(limit)
        processed = completed = failed = retried = 0
        for request in due_requests:
            processed += 1
            adapter = await self.adapters.get_adapter_by_id(request.adapter_id)
            if adapter is None:
                continue
            breaker = await self.breakers.get_or_create_breaker(adapter)
            try:
                updated = await self._execute_request(request, adapter, breaker, principal)
            except IntegrationServiceError:
                failed += 1
                continue
            if updated.status == IntegrationRequestStatus.COMPLETED.value:
                completed += 1
            elif updated.status in {IntegrationRequestStatus.RETRYING.value, IntegrationRequestStatus.QUEUED.value}:
                retried += 1
            else:
                failed += 1
        return QueueProcessResult(processed=processed, completed=completed, failed=failed, retried=retried)

    async def _execute_request(self, request: IntegrationRequest, adapter: IntegrationAdapter, breaker: IntegrationCircuitBreaker, principal: Principal) -> IntegrationRequestRead:
        provider = adapter_registry.resolve(adapter.system_code)
        if breaker.state == CircuitBreakerState.OPEN.value and breaker.opened_at and (self._now() - breaker.opened_at).total_seconds() < breaker.reset_after_seconds:
            raise IntegrationServiceError(status.HTTP_503_SERVICE_UNAVAILABLE, "INT-4002", "Circuit breaker is open", {"adapter_code": adapter.adapter_code, "state": breaker.state})
        if breaker.state == CircuitBreakerState.OPEN.value:
            breaker.state = CircuitBreakerState.HALF_OPEN.value
            breaker.half_opened_at = self._now()
            await self.breakers.update_breaker(breaker)
        request.status = IntegrationRequestStatus.PROCESSING.value
        request.sent_at = self._now()
        await self.events.create_event(IntegrationEventPayload(request_id=request.id, event_type="IntegrationProcessingStarted", old_status=IntegrationRequestStatus.QUEUED.value, new_status=request.status, payload={"adapter_code": adapter.adapter_code, "attempts": request.retry_count}))
        last_result: AdapterExecutionResult | None = None
        while request.retry_count < request.max_attempts:
            attempt_no = request.retry_count + 1
            attempt_started = self._now()
            attempt = IntegrationAttempt(
                request_id=request.id,
                attempt_no=attempt_no,
                status=IntegrationAttemptStatus.PROCESSING.value,
                adapter_code=adapter.adapter_code,
                provider_name=provider.adapter_name,
                request_payload=request.request_payload,
                response_payload={},
                started_at=attempt_started,
            )
            await self.attempts.create_attempt(attempt)
            result = await provider.execute(request, adapter, attempt_no)
            last_result = result
            attempt.completed_at = self._now()
            attempt.http_status = result.http_status
            attempt.response_payload = result.response_payload or {}
            if result.success:
                attempt.status = IntegrationAttemptStatus.SUCCEEDED.value
                request.status = IntegrationRequestStatus.COMPLETED.value
                request.response_payload = result.response_payload or {}
                request.completed_at = self._now()
                request.last_error_code = None
                request.last_error_message = None
                request.next_retry_at = None
                breaker.state = CircuitBreakerState.CLOSED.value
                breaker.failure_count = 0
                breaker.success_count += 1
                breaker.last_error_code = None
                breaker.last_error_message = None
                breaker.half_opened_at = None
                await self.breakers.update_breaker(breaker)
                await self.events.create_event(IntegrationEventPayload(request_id=request.id, event_type="IntegrationCompleted", old_status=IntegrationRequestStatus.PROCESSING.value, new_status=request.status, payload={"adapter_code": adapter.adapter_code, "external_reference": result.external_reference or request.external_reference or ""}))
                return IntegrationRequestRead.model_validate(request, from_attributes=True)
            attempt.status = IntegrationAttemptStatus.FAILED.value if not result.retryable else IntegrationAttemptStatus.RETRY_SCHEDULED.value
            attempt.error_code = result.error_code
            attempt.error_message = result.error_message
            request.retry_count += 1
            request.last_error_code = result.error_code
            request.last_error_message = result.error_message
            breaker.failure_count += 1
            breaker.last_failure_at = self._now()
            breaker.last_error_code = result.error_code
            breaker.last_error_message = result.error_message
            if breaker.failure_count >= adapter.breaker_failure_threshold:
                breaker.state = CircuitBreakerState.OPEN.value
                breaker.opened_at = self._now()
            await self.breakers.update_breaker(breaker)
            if not result.retryable or request.retry_count >= request.max_attempts:
                request.status = IntegrationRequestStatus.FAILED.value
                request.failed_at = self._now()
                request.next_retry_at = None
                await self.events.create_event(IntegrationEventPayload(request_id=request.id, event_type="IntegrationFailed", old_status=IntegrationRequestStatus.PROCESSING.value, new_status=request.status, payload={"error_code": result.error_code or "", "error_message": result.error_message or "", "adapter_code": adapter.adapter_code}))
                return IntegrationRequestRead.model_validate(request, from_attributes=True)
            request.status = IntegrationRequestStatus.RETRYING.value
            request.next_retry_at = self._now() + timedelta(seconds=self._backoff_seconds(attempt_no))
            await self.events.create_event(IntegrationEventPayload(request_id=request.id, event_type="IntegrationRetryScheduled", old_status=IntegrationRequestStatus.PROCESSING.value, new_status=request.status, payload={"attempt_no": attempt_no, "next_retry_at": request.next_retry_at.isoformat(), "adapter_code": adapter.adapter_code}))
        if last_result is not None and not last_result.success:
            request.status = IntegrationRequestStatus.DEAD_LETTERED.value
            request.failed_at = self._now()
        return IntegrationRequestRead.model_validate(request, from_attributes=True)

    async def get_request(self, request_id: UUID, principal: Principal) -> IntegrationRequestRead:
        request = await self.requests.get_request_by_id(request_id)
        if request is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration request not found")
        return IntegrationRequestRead.model_validate(request, from_attributes=True)

    async def list_requests(self, principal: Principal, adapter_id: UUID | None = None) -> list[IntegrationRequestRead]:
        self._require_admin(principal)
        if adapter_id is not None:
            requests = await self.requests.list_requests_for_adapter(adapter_id)
        else:
            requests = await self.requests.list_due_requests(100)
        return [IntegrationRequestRead.model_validate(item, from_attributes=True) for item in requests]

    async def get_attempts(self, request_id: UUID, principal: Principal) -> list[IntegrationAttemptRead]:
        request = await self.requests.get_request_by_id(request_id)
        if request is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration request not found")
        attempts = await self.attempts.list_attempts_for_request(request_id)
        return [IntegrationAttemptRead.model_validate(item, from_attributes=True) for item in attempts]

    async def get_events(self, request_id: UUID, principal: Principal) -> list[IntegrationEventRead]:
        request = await self.requests.get_request_by_id(request_id)
        if request is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration request not found")
        events = await self.events.list_events_for_request(request_id)
        return [IntegrationEventRead.model_validate(item, from_attributes=True) for item in events]

    async def list_breakers(self, principal: Principal) -> list[CircuitBreakerRead]:
        self._require_admin(principal)
        adapters = await self.adapters.list_adapters()
        breakers = []
        for adapter in adapters:
            breakers.append(CircuitBreakerRead.model_validate(await self.breakers.get_or_create_breaker(adapter), from_attributes=True))
        return breakers

    async def publish_events(self, limit: int, principal: Principal) -> PublishResult:
        self._require_admin(principal)
        pending_events = await self.events.list_pending_events(limit)
        for event in pending_events:
            event.publication_status = IntegrationEventPublicationStatus.PUBLISHED.value
            event.published_at = self._now()
        return PublishResult(published=len(pending_events))
