from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditMixin:
    created_by_actor_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    updated_by_actor_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)


class TaxBundleStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    RETIRED = "retired"


class TaxComponentType(str, Enum):
    BRACKET = "progressive_bracket"
    DEDUCTION = "deduction"
    EXEMPTION = "exemption"


class TaxRuleBundle(Base, TimestampMixin, AuditMixin):
    __tablename__ = "tax_rule_bundles"
    __table_args__ = (UniqueConstraint("rule_bundle_code", "version_number", "deleted_at", name="uq_tax_rule_bundles_code_version_deleted_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    rule_bundle_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    rule_bundle_name: Mapped[str] = mapped_column(String(255), nullable=False)
    jurisdiction_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    tax_category_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    taxpayer_class_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=TaxBundleStatus.DRAFT.value)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    approval_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rule_definition_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    bundle_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    components: Mapped[list[TaxRuleComponent]] = relationship("TaxRuleComponent", back_populates="rule_bundle", cascade="all, delete-orphan", order_by="TaxRuleComponent.sequence_no")
    brackets: Mapped[list[TaxBracket]] = relationship("TaxBracket", back_populates="rule_bundle", cascade="all, delete-orphan", order_by="TaxBracket.bracket_order")
    deductions: Mapped[list[TaxDeduction]] = relationship("TaxDeduction", back_populates="rule_bundle", cascade="all, delete-orphan")
    exemptions: Mapped[list[TaxExemption]] = relationship("TaxExemption", back_populates="rule_bundle", cascade="all, delete-orphan")


class TaxRuleComponent(Base, TimestampMixin, AuditMixin):
    __tablename__ = "tax_rule_components"
    __table_args__ = (UniqueConstraint("tax_rule_bundle_id", "component_code", "deleted_at", name="uq_tax_rule_components_code_deleted_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tax_rule_bundle_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tax_rule_bundles.id", ondelete="CASCADE"), nullable=False, index=True)
    component_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    component_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    component_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    applies_to: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    configuration: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    rule_bundle: Mapped[TaxRuleBundle] = relationship("TaxRuleBundle", back_populates="components")


class TaxBracket(Base, TimestampMixin, AuditMixin):
    __tablename__ = "tax_brackets"
    __table_args__ = (UniqueConstraint("tax_rule_bundle_id", "bracket_order", "deleted_at", name="uq_tax_brackets_order_deleted_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tax_rule_bundle_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tax_rule_bundles.id", ondelete="CASCADE"), nullable=False, index=True)
    bracket_order: Mapped[int] = mapped_column(Integer, nullable=False)
    lower_bound: Mapped[float] = mapped_column(Float, nullable=False)
    upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    marginal_rate: Mapped[float] = mapped_column(Float, nullable=False)
    base_tax: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    bracket_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    rule_bundle: Mapped[TaxRuleBundle] = relationship("TaxRuleBundle", back_populates="brackets")


class TaxDeduction(Base, TimestampMixin, AuditMixin):
    __tablename__ = "tax_deductions"
    __table_args__ = (UniqueConstraint("tax_rule_bundle_id", "deduction_code", "deleted_at", name="uq_tax_deductions_code_deleted_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tax_rule_bundle_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tax_rule_bundles.id", ondelete="CASCADE"), nullable=False, index=True)
    deduction_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    deduction_name: Mapped[str] = mapped_column(String(255), nullable=False)
    deduction_type: Mapped[str] = mapped_column(String(64), nullable=False)
    calculation_basis: Mapped[str] = mapped_column(String(120), nullable=False)
    configuration: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    priority_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    rule_bundle: Mapped[TaxRuleBundle] = relationship("TaxRuleBundle", back_populates="deductions")


class TaxExemption(Base, TimestampMixin, AuditMixin):
    __tablename__ = "tax_exemptions"
    __table_args__ = (UniqueConstraint("tax_rule_bundle_id", "exemption_code", "deleted_at", name="uq_tax_exemptions_code_deleted_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tax_rule_bundle_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tax_rule_bundles.id", ondelete="CASCADE"), nullable=False, index=True)
    exemption_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    exemption_name: Mapped[str] = mapped_column(String(255), nullable=False)
    exemption_type: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    configuration: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    priority_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    rule_bundle: Mapped[TaxRuleBundle] = relationship("TaxRuleBundle", back_populates="exemptions")


class TaxCalculation(Base, TimestampMixin):
    __tablename__ = "tax_calculations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tax_rule_bundle_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tax_rule_bundles.id", ondelete="RESTRICT"), nullable=False, index=True)
    taxpayer_subject: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    jurisdiction_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    tax_category_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    taxpayer_class_code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    assessment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    gross_income: Mapped[float] = mapped_column(Float, nullable=False)
    taxable_income: Mapped[float] = mapped_column(Float, nullable=False)
    exemptions_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    deductions_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tax_amount: Mapped[float] = mapped_column(Float, nullable=False)
    effective_tax_rate: Mapped[float] = mapped_column(Float, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(16), nullable=False, default="NPR")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    explanation: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)


class TaxAuditEvent(Base, TimestampMixin):
    __tablename__ = "tax_audit_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    actor_subject: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    aggregate_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    action: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    details: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    correlation_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
