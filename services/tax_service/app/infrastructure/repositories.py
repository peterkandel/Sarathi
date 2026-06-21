from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import TaxAuditEventPayload
from app.domain.models import TaxAuditEvent, TaxBracket, TaxCalculation, TaxDeduction, TaxExemption, TaxRuleBundle, TaxRuleComponent


class TaxRuleBundleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_bundle(self, bundle: TaxRuleBundle) -> TaxRuleBundle:
        self.session.add(bundle)
        await self.session.flush()
        return bundle

    async def update_bundle(self, bundle: TaxRuleBundle) -> TaxRuleBundle:
        self.session.add(bundle)
        await self.session.flush()
        return bundle

    async def get_bundle_by_id(self, bundle_id: UUID) -> TaxRuleBundle | None:
        result = await self.session.execute(select(TaxRuleBundle).where(TaxRuleBundle.id == bundle_id))
        return result.scalar_one_or_none()

    async def list_bundles(self) -> Sequence[TaxRuleBundle]:
        result = await self.session.execute(select(TaxRuleBundle).where(TaxRuleBundle.deleted_at.is_(None)).order_by(TaxRuleBundle.created_at.desc()))
        return list(result.scalars().all())

    async def find_applicable_bundle(self, jurisdiction_code: str, tax_category_code: str, taxpayer_class_code: str, assessment_date: date) -> TaxRuleBundle | None:
        result = await self.session.execute(
            select(TaxRuleBundle)
            .where(
                TaxRuleBundle.jurisdiction_code == jurisdiction_code,
                TaxRuleBundle.tax_category_code == tax_category_code,
                TaxRuleBundle.taxpayer_class_code == taxpayer_class_code,
                TaxRuleBundle.status == "active",
                TaxRuleBundle.deleted_at.is_(None),
                TaxRuleBundle.effective_from <= assessment_date,
                and_(TaxRuleBundle.effective_to.is_(None), True) | (TaxRuleBundle.effective_to >= assessment_date),
            )
            .order_by(TaxRuleBundle.version_number.desc())
        )
        return result.scalars().first()


class TaxBracketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_bracket(self, bracket: TaxBracket) -> TaxBracket:
        self.session.add(bracket)
        await self.session.flush()
        return bracket

    async def list_brackets_for_bundle(self, tax_rule_bundle_id: UUID) -> Sequence[TaxBracket]:
        result = await self.session.execute(select(TaxBracket).where(TaxBracket.tax_rule_bundle_id == tax_rule_bundle_id, TaxBracket.deleted_at.is_(None)).order_by(TaxBracket.bracket_order.asc()))
        return list(result.scalars().all())


class TaxDeductionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_deduction(self, deduction: TaxDeduction) -> TaxDeduction:
        self.session.add(deduction)
        await self.session.flush()
        return deduction

    async def list_deductions_for_bundle(self, tax_rule_bundle_id: UUID) -> Sequence[TaxDeduction]:
        result = await self.session.execute(select(TaxDeduction).where(TaxDeduction.tax_rule_bundle_id == tax_rule_bundle_id, TaxDeduction.deleted_at.is_(None)).order_by(TaxDeduction.priority_order.asc()))
        return list(result.scalars().all())


class TaxExemptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_exemption(self, exemption: TaxExemption) -> TaxExemption:
        self.session.add(exemption)
        await self.session.flush()
        return exemption

    async def list_exemptions_for_bundle(self, tax_rule_bundle_id: UUID) -> Sequence[TaxExemption]:
        result = await self.session.execute(select(TaxExemption).where(TaxExemption.tax_rule_bundle_id == tax_rule_bundle_id, TaxExemption.deleted_at.is_(None)).order_by(TaxExemption.priority_order.asc()))
        return list(result.scalars().all())


class TaxCalculationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_calculation(self, calculation: TaxCalculation) -> TaxCalculation:
        self.session.add(calculation)
        await self.session.flush()
        return calculation

    async def get_calculation_by_id(self, calculation_id: UUID) -> TaxCalculation | None:
        result = await self.session.execute(select(TaxCalculation).where(TaxCalculation.id == calculation_id))
        return result.scalar_one_or_none()

    async def list_calculations_for_subject(self, taxpayer_subject: str) -> Sequence[TaxCalculation]:
        result = await self.session.execute(select(TaxCalculation).where(TaxCalculation.taxpayer_subject == taxpayer_subject).order_by(TaxCalculation.created_at.desc()))
        return list(result.scalars().all())


class TaxAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(self, event: TaxAuditEventPayload) -> TaxAuditEvent:
        audit_event = TaxAuditEvent(
            event_type=event.event_type,
            actor_subject=event.actor_subject,
            aggregate_id=event.aggregate_id,
            action=event.action,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            outcome=event.outcome,
            payload=event.payload,
            details=event.details,
            correlation_id=event.correlation_id,
        )
        self.session.add(audit_event)
        await self.session.flush()
        return audit_event

    async def list_events_for_resource(self, resource_type: str, resource_id: str) -> Sequence[TaxAuditEvent]:
        result = await self.session.execute(select(TaxAuditEvent).where(TaxAuditEvent.resource_type == resource_type, TaxAuditEvent.resource_id == resource_id).order_by(TaxAuditEvent.created_at.asc()))
        return list(result.scalars().all())
