from __future__ import annotations

from dataclasses import dataclass

from app.domain.models import IntegrationAdapter, IntegrationRequest
from app.domain.ports import AdapterExecutionResult, IntegrationAdapterProtocol


@dataclass(slots=True)
class BaseIntegrationAdapter(IntegrationAdapterProtocol):
    adapter_name: str
    system_code: str

    async def execute(self, request: IntegrationRequest, adapter: IntegrationAdapter, attempt_no: int) -> AdapterExecutionResult:
        simulate_failures = int(request.request_payload.get("simulate_failure_attempts", 0) or 0)
        permanent_error = bool(request.request_payload.get("force_permanent_error", False))
        if permanent_error:
            return AdapterExecutionResult(
                success=False,
                retryable=False,
                http_status=400,
                error_code="INTEGRATION-PERMANENT",
                error_message=f"Permanent error for {self.system_code}",
                response_payload={"system_code": self.system_code, "attempt_no": attempt_no},
            )
        if attempt_no <= simulate_failures:
            return AdapterExecutionResult(
                success=False,
                retryable=True,
                http_status=503,
                error_code="INTEGRATION-RETRYABLE",
                error_message=f"Retryable error for {self.system_code}",
                response_payload={"system_code": self.system_code, "attempt_no": attempt_no},
            )
        external_reference = request.external_reference or f"{self.system_code}-{request.id}"
        return AdapterExecutionResult(
            success=True,
            retryable=False,
            http_status=200,
            external_reference=external_reference,
            response_payload={"system_code": self.system_code, "attempt_no": attempt_no, "adapter_code": adapter.adapter_code},
        )


class CitizenshipRegistryAdapter(BaseIntegrationAdapter):
    def __init__(self) -> None:
        super().__init__(adapter_name="citizenship_registry_adapter", system_code="citizenship_registry")


class TaxAuthorityAdapter(BaseIntegrationAdapter):
    def __init__(self) -> None:
        super().__init__(adapter_name="tax_authority_adapter", system_code="tax_authority")


class PassportSystemAdapter(BaseIntegrationAdapter):
    def __init__(self) -> None:
        super().__init__(adapter_name="passport_system_adapter", system_code="passport_system")


class PaymentSystemAdapter(BaseIntegrationAdapter):
    def __init__(self) -> None:
        super().__init__(adapter_name="payment_system_adapter", system_code="payment_system")


class IntegrationAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, IntegrationAdapterProtocol] = {
            "citizenship_registry": CitizenshipRegistryAdapter(),
            "tax_authority": TaxAuthorityAdapter(),
            "passport_system": PassportSystemAdapter(),
            "payment_system": PaymentSystemAdapter(),
        }

    def resolve(self, system_code: str) -> IntegrationAdapterProtocol:
        adapter = self._adapters.get(system_code)
        if adapter is None:
            raise ValueError(f"Unsupported integration system: {system_code}")
        return adapter


adapter_registry = IntegrationAdapterRegistry()
