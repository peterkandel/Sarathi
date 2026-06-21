from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import TaxService
from app.infrastructure.db import get_session
from app.infrastructure.repositories import TaxAuditRepository, TaxBracketRepository, TaxCalculationRepository, TaxDeductionRepository, TaxExemptionRepository, TaxRuleBundleRepository


async def get_tax_rule_bundle_repository(session: AsyncSession = Depends(get_session)) -> TaxRuleBundleRepository:
    return TaxRuleBundleRepository(session)


async def get_tax_bracket_repository(session: AsyncSession = Depends(get_session)) -> TaxBracketRepository:
    return TaxBracketRepository(session)


async def get_tax_deduction_repository(session: AsyncSession = Depends(get_session)) -> TaxDeductionRepository:
    return TaxDeductionRepository(session)


async def get_tax_exemption_repository(session: AsyncSession = Depends(get_session)) -> TaxExemptionRepository:
    return TaxExemptionRepository(session)


async def get_tax_calculation_repository(session: AsyncSession = Depends(get_session)) -> TaxCalculationRepository:
    return TaxCalculationRepository(session)


async def get_tax_audit_repository(session: AsyncSession = Depends(get_session)) -> TaxAuditRepository:
    return TaxAuditRepository(session)


async def get_tax_service(
    bundle_repository: TaxRuleBundleRepository = Depends(get_tax_rule_bundle_repository),
    bracket_repository: TaxBracketRepository = Depends(get_tax_bracket_repository),
    deduction_repository: TaxDeductionRepository = Depends(get_tax_deduction_repository),
    exemption_repository: TaxExemptionRepository = Depends(get_tax_exemption_repository),
    calculation_repository: TaxCalculationRepository = Depends(get_tax_calculation_repository),
    audit_repository: TaxAuditRepository = Depends(get_tax_audit_repository),
) -> TaxService:
    return TaxService(bundle_repository, bracket_repository, deduction_repository, exemption_repository, calculation_repository, audit_repository)
