from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaxRuleBundleCreate(BaseModel):
    rule_bundle_code: str = Field(min_length=1, max_length=120)
    rule_bundle_name: str = Field(min_length=1, max_length=255)
    jurisdiction_code: str = Field(min_length=1, max_length=120)
    tax_category_code: str = Field(min_length=1, max_length=120)
    taxpayer_class_code: str = Field(min_length=1, max_length=120)
    version_number: int = Field(ge=1)
    status: str = Field(default="draft", max_length=32)
    effective_from: date
    effective_to: date | None = None
    approval_reference: str | None = Field(default=None, max_length=255)
    rule_definition_hash: str = Field(min_length=1, max_length=128)
    bundle_metadata: dict[str, object] = Field(default_factory=dict)


class TaxRuleBundleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_bundle_code: str
    rule_bundle_name: str
    jurisdiction_code: str
    tax_category_code: str
    taxpayer_class_code: str
    version_number: int
    status: str
    effective_from: date
    effective_to: date | None
    approval_reference: str | None
    rule_definition_hash: str
    bundle_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class TaxBracketCreate(BaseModel):
    bracket_order: int = Field(ge=1)
    lower_bound: float = Field(ge=0)
    upper_bound: float | None = Field(default=None)
    marginal_rate: float = Field(ge=0, le=1)
    base_tax: float = Field(default=0)
    bracket_metadata: dict[str, object] = Field(default_factory=dict)


class TaxBracketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tax_rule_bundle_id: UUID
    bracket_order: int
    lower_bound: float
    upper_bound: float | None
    marginal_rate: float
    base_tax: float
    bracket_metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class TaxDeductionCreate(BaseModel):
    deduction_code: str = Field(min_length=1, max_length=120)
    deduction_name: str = Field(min_length=1, max_length=255)
    deduction_type: str = Field(min_length=1, max_length=64)
    calculation_basis: str = Field(min_length=1, max_length=120)
    configuration: dict[str, object] = Field(default_factory=dict)
    priority_order: int = Field(default=0, ge=0)


class TaxDeductionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tax_rule_bundle_id: UUID
    deduction_code: str
    deduction_name: str
    deduction_type: str
    calculation_basis: str
    configuration: dict[str, object]
    priority_order: int
    created_at: datetime
    updated_at: datetime


class TaxExemptionCreate(BaseModel):
    exemption_code: str = Field(min_length=1, max_length=120)
    exemption_name: str = Field(min_length=1, max_length=255)
    exemption_type: str = Field(min_length=1, max_length=64)
    amount: float | None = None
    percentage: float | None = Field(default=None, ge=0, le=1)
    configuration: dict[str, object] = Field(default_factory=dict)
    priority_order: int = Field(default=0, ge=0)


class TaxExemptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tax_rule_bundle_id: UUID
    exemption_code: str
    exemption_name: str
    exemption_type: str
    amount: float | None
    percentage: float | None
    configuration: dict[str, object]
    priority_order: int
    created_at: datetime
    updated_at: datetime


class TaxCalculationInput(BaseModel):
    taxpayer_subject: str = Field(min_length=1, max_length=120)
    jurisdiction_code: str = Field(min_length=1, max_length=120)
    tax_category_code: str = Field(min_length=1, max_length=120)
    taxpayer_class_code: str = Field(min_length=1, max_length=120)
    assessment_date: date
    gross_income: float = Field(ge=0)
    declared_deductions: dict[str, float] = Field(default_factory=dict)
    declared_exemptions: dict[str, float] = Field(default_factory=dict)
    currency_code: str = Field(default="NPR", max_length=16)


class TaxCalculationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tax_rule_bundle_id: UUID
    taxpayer_subject: str
    jurisdiction_code: str
    tax_category_code: str
    taxpayer_class_code: str
    assessment_date: date
    gross_income: float
    taxable_income: float
    exemptions_total: float
    deductions_total: float
    tax_amount: float
    effective_tax_rate: float
    currency_code: str
    confidence_score: float
    status: str
    explanation: dict[str, object]
    created_at: datetime
    updated_at: datetime


class TaxCalculationSummary(BaseModel):
    calculation_id: UUID
    tax_amount: float
    taxable_income: float
    effective_tax_rate: float
    confidence_score: float
    status: str
    rule_bundle_code: str
    rule_bundle_version: int


class TaxAuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    actor_subject: str | None
    aggregate_id: UUID | None
    action: str | None
    resource_type: str | None
    resource_id: str | None
    outcome: str | None
    payload: dict[str, object]
    details: dict[str, object]
    correlation_id: str | None
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str
