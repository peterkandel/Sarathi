from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.core.config import settings
from app.domain.events import CalculationTraceEntry, TaxAuditEventPayload, TaxErrorPayload, ValidationIssue
from app.domain.models import TaxAuditEvent, TaxBracket, TaxCalculation, TaxComponentType, TaxDeduction, TaxExemption, TaxRuleBundle, TaxRuleComponent, TaxBundleStatus
from app.domain.ports import TaxAuditRepositoryProtocol, TaxBracketRepositoryProtocol, TaxCalculationRepositoryProtocol, TaxDeductionRepositoryProtocol, TaxExemptionRepositoryProtocol, TaxRuleBundleRepositoryProtocol
from app.domain.schemas import TaxAuditEventRead, TaxBracketCreate, TaxBracketRead, TaxCalculationInput, TaxCalculationRead, TaxCalculationSummary, TaxDeductionCreate, TaxDeductionRead, TaxExemptionCreate, TaxExemptionRead, TaxRuleBundleCreate, TaxRuleBundleRead
from shared_auth import Role
from shared_auth.models import Principal
from shared_auth.security import has_any_role


ADMIN_ROLES = (Role.ADMINISTRATOR, Role.SUPER_ADMINISTRATOR)


class TaxEngineError(HTTPException):
    def __init__(self, status_code: int, error_code: str, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(status_code=status_code, detail={"error_code": error_code, "message": message, "details": details or {}})
        self.error_code = error_code
        self.message = message
        self.details = details or {}


class TaxService:
    def __init__(
        self,
        bundles: TaxRuleBundleRepositoryProtocol,
        brackets: TaxBracketRepositoryProtocol,
        deductions: TaxDeductionRepositoryProtocol,
        exemptions: TaxExemptionRepositoryProtocol,
        calculations: TaxCalculationRepositoryProtocol,
        audit: TaxAuditRepositoryProtocol,
    ) -> None:
        self.bundles = bundles
        self.brackets = brackets
        self.deductions = deductions
        self.exemptions = exemptions
        self.calculations = calculations
        self.audit = audit

    def _is_admin(self, principal: Principal) -> bool:
        return has_any_role(principal, ADMIN_ROLES)

    def _require_admin(self, principal: Principal) -> None:
        if not self._is_admin(principal):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrative role required")

    def _round(self, value: float) -> float:
        return round(value, settings.rounding_precision)

    async def create_bundle(self, payload: TaxRuleBundleCreate, principal: Principal) -> TaxRuleBundle:
        self._require_admin(principal)
        bundle = TaxRuleBundle(
            rule_bundle_code=payload.rule_bundle_code,
            rule_bundle_name=payload.rule_bundle_name,
            jurisdiction_code=payload.jurisdiction_code,
            tax_category_code=payload.tax_category_code,
            taxpayer_class_code=payload.taxpayer_class_code,
            version_number=payload.version_number,
            status=payload.status,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            approval_reference=payload.approval_reference,
            rule_definition_hash=payload.rule_definition_hash,
            bundle_metadata=payload.bundle_metadata,
            created_by_actor_id=None,
            updated_by_actor_id=None,
        )
        created = await self.bundles.create_bundle(bundle)
        await self.audit.record_event(TaxAuditEventPayload(event_type="TaxRuleBundleCreated", actor_subject=principal.subject, aggregate_id=created.id, action="create_bundle", resource_type="tax_rule_bundle", resource_id=str(created.id), outcome="success", payload={"rule_bundle_code": created.rule_bundle_code, "version_number": created.version_number}))
        return created

    async def list_bundles(self, principal: Principal) -> list[TaxRuleBundle]:
        self._require_admin(principal)
        return list(await self.bundles.list_bundles())

    async def get_bundle(self, bundle_id: UUID, principal: Principal) -> TaxRuleBundle:
        bundle = await self.bundles.get_bundle_by_id(bundle_id)
        if bundle is None or bundle.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax rule bundle not found")
        if not self._is_admin(principal) and bundle.status != TaxBundleStatus.ACTIVE.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tax rule bundle access denied")
        return bundle

    async def create_bracket(self, bundle_id: UUID, payload: TaxBracketCreate, principal: Principal) -> TaxBracket:
        self._require_admin(principal)
        bundle = await self.get_bundle(bundle_id, principal)
        bracket = TaxBracket(
            tax_rule_bundle_id=bundle.id,
            bracket_order=payload.bracket_order,
            lower_bound=payload.lower_bound,
            upper_bound=payload.upper_bound,
            marginal_rate=payload.marginal_rate,
            base_tax=payload.base_tax,
            bracket_metadata=payload.bracket_metadata,
            created_by_actor_id=None,
            updated_by_actor_id=None,
        )
        created = await self.brackets.create_bracket(bracket)
        await self.audit.record_event(TaxAuditEventPayload(event_type="TaxBracketCreated", actor_subject=principal.subject, aggregate_id=created.id, action="create_bracket", resource_type="tax_bracket", resource_id=str(created.id), outcome="success", payload={"bundle_id": str(bundle.id)}))
        return created

    async def create_deduction(self, bundle_id: UUID, payload: TaxDeductionCreate, principal: Principal) -> TaxDeduction:
        self._require_admin(principal)
        bundle = await self.get_bundle(bundle_id, principal)
        deduction = TaxDeduction(
            tax_rule_bundle_id=bundle.id,
            deduction_code=payload.deduction_code,
            deduction_name=payload.deduction_name,
            deduction_type=payload.deduction_type,
            calculation_basis=payload.calculation_basis,
            configuration=payload.configuration,
            priority_order=payload.priority_order,
            created_by_actor_id=None,
            updated_by_actor_id=None,
        )
        created = await self.deductions.create_deduction(deduction)
        await self.audit.record_event(TaxAuditEventPayload(event_type="TaxDeductionCreated", actor_subject=principal.subject, aggregate_id=created.id, action="create_deduction", resource_type="tax_deduction", resource_id=str(created.id), outcome="success", payload={"bundle_id": str(bundle.id)}))
        return created

    async def create_exemption(self, bundle_id: UUID, payload: TaxExemptionCreate, principal: Principal) -> TaxExemption:
        self._require_admin(principal)
        bundle = await self.get_bundle(bundle_id, principal)
        exemption = TaxExemption(
            tax_rule_bundle_id=bundle.id,
            exemption_code=payload.exemption_code,
            exemption_name=payload.exemption_name,
            exemption_type=payload.exemption_type,
            amount=payload.amount,
            percentage=payload.percentage,
            configuration=payload.configuration,
            priority_order=payload.priority_order,
            created_by_actor_id=None,
            updated_by_actor_id=None,
        )
        created = await self.exemptions.create_exemption(exemption)
        await self.audit.record_event(TaxAuditEventPayload(event_type="TaxExemptionCreated", actor_subject=principal.subject, aggregate_id=created.id, action="create_exemption", resource_type="tax_exemption", resource_id=str(created.id), outcome="success", payload={"bundle_id": str(bundle.id)}))
        return created

    async def calculate_tax(self, payload: TaxCalculationInput, principal: Principal) -> TaxCalculationRead:
        bundle = await self.bundles.find_applicable_bundle(payload.jurisdiction_code, payload.tax_category_code, payload.taxpayer_class_code, payload.assessment_date)
        if bundle is None:
            raise TaxEngineError(status.HTTP_404_NOT_FOUND, "TAX-4001", "No applicable tax rule bundle found", {"jurisdiction_code": payload.jurisdiction_code, "tax_category_code": payload.tax_category_code, "taxpayer_class_code": payload.taxpayer_class_code})

        exemptions = await self.exemptions.list_exemptions_for_bundle(bundle.id)
        deductions = await self.deductions.list_deductions_for_bundle(bundle.id)
        brackets = await self.brackets.list_brackets_for_bundle(bundle.id)
        if not brackets:
            raise TaxEngineError(status.HTTP_400_BAD_REQUEST, "TAX-4002", "Rule bundle has no brackets", {"bundle_id": str(bundle.id)})

        trace: list[CalculationTraceEntry] = [CalculationTraceEntry(step="bundle_resolution", description="Resolved applicable tax rule bundle", metadata={"bundle_code": bundle.rule_bundle_code, "version_number": bundle.version_number})]
        gross_income = payload.gross_income
        exemptions_total = self._calculate_exemptions(exemptions, payload.declared_exemptions, gross_income, trace)
        deductions_total = self._calculate_deductions(deductions, payload.declared_deductions, gross_income - exemptions_total, trace)
        taxable_income = max(0.0, gross_income - exemptions_total - deductions_total)
        tax_amount, bracket_trace = self._calculate_bracket_tax(brackets, taxable_income)
        trace.extend(bracket_trace)
        effective_tax_rate = 0.0 if taxable_income <= 0 else self._round(tax_amount / taxable_income)
        confidence_score = self._calculate_confidence(brackets, deductions, exemptions, trace)
        status_value = "completed" if confidence_score >= 0.75 else "review_required"
        explanation = {
            "trace": [entry.model_dump() for entry in trace],
            "bundle": {"rule_bundle_code": bundle.rule_bundle_code, "version_number": bundle.version_number, "status": bundle.status},
            "inputs": payload.model_dump(mode="json"),
            "outputs": {
                "gross_income": gross_income,
                "taxable_income": taxable_income,
                "tax_amount": tax_amount,
                "effective_tax_rate": effective_tax_rate,
                "confidence_score": confidence_score,
                "status": status_value,
            },
            "rule_counts": {"brackets": len(brackets), "deductions": len(deductions), "exemptions": len(exemptions)},
        }
        calculation = TaxCalculation(
            tax_rule_bundle_id=bundle.id,
            taxpayer_subject=principal.subject,
            jurisdiction_code=payload.jurisdiction_code,
            tax_category_code=payload.tax_category_code,
            taxpayer_class_code=payload.taxpayer_class_code,
            assessment_date=payload.assessment_date,
            gross_income=gross_income,
            taxable_income=taxable_income,
            exemptions_total=exemptions_total,
            deductions_total=deductions_total,
            tax_amount=tax_amount,
            effective_tax_rate=effective_tax_rate,
            currency_code=payload.currency_code,
            confidence_score=confidence_score,
            status=status_value,
            explanation=explanation,
        )
        created = await self.calculations.create_calculation(calculation)
        await self.audit.record_event(TaxAuditEventPayload(event_type="TaxCalculationCompleted", actor_subject=principal.subject, aggregate_id=created.id, action="calculate_tax", resource_type="tax_calculation", resource_id=str(created.id), outcome="success", payload={"bundle_code": bundle.rule_bundle_code, "version_number": bundle.version_number, "tax_amount": tax_amount, "confidence_score": confidence_score}))
        return TaxCalculationRead.model_validate(created, from_attributes=True)

    async def get_calculation(self, calculation_id: UUID, principal: Principal) -> TaxCalculationRead:
        calculation = await self.calculations.get_calculation_by_id(calculation_id)
        if calculation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax calculation not found")
        if calculation.taxpayer_subject != principal.subject and not self._is_admin(principal):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tax calculation access denied")
        return TaxCalculationRead.model_validate(calculation, from_attributes=True)

    async def list_calculations(self, principal: Principal) -> list[TaxCalculationRead]:
        if self._is_admin(principal):
            calculations = await self.calculations.list_calculations_for_subject(principal.subject)
            return [TaxCalculationRead.model_validate(calculation, from_attributes=True) for calculation in calculations]
        calculations = await self.calculations.list_calculations_for_subject(principal.subject)
        return [TaxCalculationRead.model_validate(calculation, from_attributes=True) for calculation in calculations]

    async def list_audit_events(self, resource_type: str, resource_id: str, principal: Principal) -> list[TaxAuditEventRead]:
        if not self._is_admin(principal):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Audit access denied")
        return [TaxAuditEventRead.model_validate(event, from_attributes=True) for event in await self.audit.list_events_for_resource(resource_type, resource_id)]

    def _calculate_exemptions(self, exemptions: list[TaxExemption], declared_exemptions: dict[str, float], gross_income: float, trace: list[CalculationTraceEntry]) -> float:
        total = 0.0
        for exemption in exemptions:
            declared_amount = declared_exemptions.get(exemption.exemption_code, 0.0)
            if exemption.exemption_type == "fixed_amount":
                applied = min(exemption.amount or 0.0, gross_income)
            elif exemption.exemption_type == "percentage":
                applied = gross_income * float(exemption.percentage or 0.0)
            else:
                applied = declared_amount
            total += applied
            trace.append(CalculationTraceEntry(step="exemption", description=f"Applied exemption {exemption.exemption_code}", amount=self._round(applied), metadata={"exemption_type": exemption.exemption_type}))
        return self._round(total)

    def _calculate_deductions(self, deductions: list[TaxDeduction], declared_deductions: dict[str, float], taxable_base: float, trace: list[CalculationTraceEntry]) -> float:
        total = 0.0
        for deduction in deductions:
            declared_amount = declared_deductions.get(deduction.deduction_code, 0.0)
            if deduction.deduction_type == "fixed_amount":
                applied = min(float(deduction.configuration.get("amount", declared_amount)), taxable_base)
            elif deduction.deduction_type == "percentage":
                applied = taxable_base * float(deduction.configuration.get("rate", declared_amount))
            elif deduction.deduction_type == "capped_percentage":
                raw_amount = taxable_base * float(deduction.configuration.get("rate", declared_amount))
                applied = min(raw_amount, float(deduction.configuration.get("cap", raw_amount)))
            else:
                applied = declared_amount
            total += applied
            trace.append(CalculationTraceEntry(step="deduction", description=f"Applied deduction {deduction.deduction_code}", amount=self._round(applied), metadata={"deduction_type": deduction.deduction_type}))
        return self._round(total)

    def _calculate_bracket_tax(self, brackets: list[TaxBracket], taxable_income: float) -> tuple[float, list[CalculationTraceEntry]]:
        tax_amount = 0.0
        trace: list[CalculationTraceEntry] = []
        for bracket in brackets:
            if taxable_income <= bracket.lower_bound:
                continue
            upper_bound = bracket.upper_bound if bracket.upper_bound is not None else taxable_income
            amount_in_bracket = max(0.0, min(taxable_income, upper_bound) - bracket.lower_bound)
            bracket_tax = bracket.base_tax + (amount_in_bracket * bracket.marginal_rate)
            tax_amount = max(tax_amount, bracket_tax)
            trace.append(CalculationTraceEntry(step="bracket", description=f"Applied bracket {bracket.bracket_order}", amount=self._round(bracket_tax), metadata={"lower_bound": bracket.lower_bound, "upper_bound": bracket.upper_bound, "marginal_rate": bracket.marginal_rate}))
        return self._round(tax_amount), trace

    def _calculate_confidence(self, brackets: list[TaxBracket], deductions: list[TaxDeduction], exemptions: list[TaxExemption], trace: list[CalculationTraceEntry]) -> float:
        component_count = len(brackets) + len(deductions) + len(exemptions)
        if component_count == 0:
            return 0.0
        raw = min(1.0, 0.5 + (0.1 * len(brackets)) + (0.05 * len(deductions)) + (0.05 * len(exemptions)) + min(0.2, len(trace) * 0.01))
        return self._round(raw)
