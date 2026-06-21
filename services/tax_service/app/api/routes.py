from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import get_tax_service
from app.application.services import TaxService
from app.domain.schemas import MessageResponse, TaxAuditEventRead, TaxBracketCreate, TaxBracketRead, TaxCalculationInput, TaxCalculationRead, TaxCalculationSummary, TaxDeductionCreate, TaxDeductionRead, TaxExemptionCreate, TaxExemptionRead, TaxRuleBundleCreate, TaxRuleBundleRead
from shared_auth import get_principal


router = APIRouter(tags=["tax"])


@router.post("/rule-bundles", response_model=TaxRuleBundleRead, status_code=status.HTTP_201_CREATED)
async def create_rule_bundle(request: Request, payload: TaxRuleBundleCreate, service: TaxService = Depends(get_tax_service)) -> TaxRuleBundleRead:
    bundle = await service.create_bundle(payload, get_principal(request))
    return TaxRuleBundleRead.model_validate(bundle, from_attributes=True)


@router.get("/rule-bundles", response_model=list[TaxRuleBundleRead])
async def list_rule_bundles(request: Request, service: TaxService = Depends(get_tax_service)) -> list[TaxRuleBundleRead]:
    bundles = await service.list_bundles(get_principal(request))
    return [TaxRuleBundleRead.model_validate(bundle, from_attributes=True) for bundle in bundles]


@router.get("/rule-bundles/{bundle_id}", response_model=TaxRuleBundleRead)
async def get_rule_bundle(bundle_id: UUID, request: Request, service: TaxService = Depends(get_tax_service)) -> TaxRuleBundleRead:
    bundle = await service.get_bundle(bundle_id, get_principal(request))
    return TaxRuleBundleRead.model_validate(bundle, from_attributes=True)


@router.post("/rule-bundles/{bundle_id}/brackets", response_model=TaxBracketRead, status_code=status.HTTP_201_CREATED)
async def create_bracket(bundle_id: UUID, request: Request, payload: TaxBracketCreate, service: TaxService = Depends(get_tax_service)) -> TaxBracketRead:
    bracket = await service.create_bracket(bundle_id, payload, get_principal(request))
    return TaxBracketRead.model_validate(bracket, from_attributes=True)


@router.post("/rule-bundles/{bundle_id}/deductions", response_model=TaxDeductionRead, status_code=status.HTTP_201_CREATED)
async def create_deduction(bundle_id: UUID, request: Request, payload: TaxDeductionCreate, service: TaxService = Depends(get_tax_service)) -> TaxDeductionRead:
    deduction = await service.create_deduction(bundle_id, payload, get_principal(request))
    return TaxDeductionRead.model_validate(deduction, from_attributes=True)


@router.post("/rule-bundles/{bundle_id}/exemptions", response_model=TaxExemptionRead, status_code=status.HTTP_201_CREATED)
async def create_exemption(bundle_id: UUID, request: Request, payload: TaxExemptionCreate, service: TaxService = Depends(get_tax_service)) -> TaxExemptionRead:
    exemption = await service.create_exemption(bundle_id, payload, get_principal(request))
    return TaxExemptionRead.model_validate(exemption, from_attributes=True)


@router.post("/calculations", response_model=TaxCalculationRead, status_code=status.HTTP_201_CREATED)
async def calculate_tax(request: Request, payload: TaxCalculationInput, service: TaxService = Depends(get_tax_service)) -> TaxCalculationRead:
    return await service.calculate_tax(payload, get_principal(request))


@router.get("/calculations/{calculation_id}", response_model=TaxCalculationRead)
async def get_calculation(calculation_id: UUID, request: Request, service: TaxService = Depends(get_tax_service)) -> TaxCalculationRead:
    return await service.get_calculation(calculation_id, get_principal(request))


@router.get("/calculations", response_model=list[TaxCalculationRead])
async def list_calculations(request: Request, service: TaxService = Depends(get_tax_service)) -> list[TaxCalculationRead]:
    return await service.list_calculations(get_principal(request))


@router.get("/calculations/{calculation_id}/audit-events", response_model=list[TaxAuditEventRead])
async def list_audit_events(calculation_id: UUID, request: Request, service: TaxService = Depends(get_tax_service)) -> list[TaxAuditEventRead]:
    return await service.list_audit_events("tax_calculation", str(calculation_id), get_principal(request))


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "tax_service"}
