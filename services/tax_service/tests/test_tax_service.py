from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.api.dependencies import get_tax_service
from app.domain.models import TaxAuditEvent
from app.main import app


class CitizenHeaders:
    @staticmethod
    def value(subject: str = "citizen-001") -> dict[str, str]:
        return {
            "x-sarathi-subject": subject,
            "x-sarathi-roles": "Citizen",
            "x-sarathi-agency-id": "agency-01",
        }


class AdminHeaders:
    @staticmethod
    def value(subject: str = "admin-001") -> dict[str, str]:
        return {
            "x-sarathi-subject": subject,
            "x-sarathi-roles": "Administrator",
            "x-sarathi-agency-id": "agency-01",
        }


@pytest.mark.asyncio
async def test_create_bundle_and_calculate_tax(client: AsyncClient):
    bundle_response = await client.post(
        "/tax/v1/rule-bundles",
        headers=AdminHeaders.value(),
        json={
            "rule_bundle_code": "income-tax",
            "rule_bundle_name": "Income Tax 2026",
            "jurisdiction_code": "NP",
            "tax_category_code": "PERSONAL_INCOME",
            "taxpayer_class_code": "RESIDENT",
            "version_number": 1,
            "status": "active",
            "effective_from": "2026-01-01",
            "rule_definition_hash": "hash-001",
            "bundle_metadata": {"source": "law-2026"},
        },
    )
    assert bundle_response.status_code == 201
    bundle_id = bundle_response.json()["id"]

    bracket_one = await client.post(
        f"/tax/v1/rule-bundles/{bundle_id}/brackets",
        headers=AdminHeaders.value(),
        json={"bracket_order": 1, "lower_bound": 0, "upper_bound": 500000, "marginal_rate": 0.05, "base_tax": 0},
    )
    assert bracket_one.status_code == 201

    bracket_two = await client.post(
        f"/tax/v1/rule-bundles/{bundle_id}/brackets",
        headers=AdminHeaders.value(),
        json={"bracket_order": 2, "lower_bound": 500000, "upper_bound": None, "marginal_rate": 0.1, "base_tax": 25000},
    )
    assert bracket_two.status_code == 201

    deduction_response = await client.post(
        f"/tax/v1/rule-bundles/{bundle_id}/deductions",
        headers=AdminHeaders.value(),
        json={
            "deduction_code": "retirement_savings",
            "deduction_name": "Retirement Savings",
            "deduction_type": "fixed_amount",
            "calculation_basis": "income",
            "configuration": {"amount": 50000},
        },
    )
    assert deduction_response.status_code == 201

    exemption_response = await client.post(
        f"/tax/v1/rule-bundles/{bundle_id}/exemptions",
        headers=AdminHeaders.value(),
        json={
            "exemption_code": "senior_allowance",
            "exemption_name": "Senior Allowance",
            "exemption_type": "fixed_amount",
            "amount": 20000,
        },
    )
    assert exemption_response.status_code == 201

    calculation_response = await client.post(
        "/tax/v1/calculations",
        headers=CitizenHeaders.value(),
        json={
            "taxpayer_subject": "citizen-001",
            "jurisdiction_code": "NP",
            "tax_category_code": "PERSONAL_INCOME",
            "taxpayer_class_code": "RESIDENT",
            "assessment_date": "2026-06-21",
            "gross_income": 700000,
            "declared_deductions": {"retirement_savings": 50000},
            "declared_exemptions": {"senior_allowance": 20000},
            "currency_code": "NPR",
        },
    )
    assert calculation_response.status_code == 201
    body = calculation_response.json()
    assert body["taxable_income"] == 630000
    assert body["tax_amount"] > 0
    assert body["confidence_score"] >= 0.75
    assert body["status"] in {"completed", "review_required"}

    calculation_id = body["id"]
    get_response = await client.get(f"/tax/v1/calculations/{calculation_id}", headers=CitizenHeaders.value())
    assert get_response.status_code == 200
    assert get_response.json()["id"] == calculation_id


@pytest.mark.asyncio
async def test_audit_and_access_control(client: AsyncClient):
    bundle_response = await client.post(
        "/tax/v1/rule-bundles",
        headers=AdminHeaders.value("admin-002"),
        json={
            "rule_bundle_code": "sales-tax",
            "rule_bundle_name": "Sales Tax 2026",
            "jurisdiction_code": "NP",
            "tax_category_code": "SALES_TAX",
            "taxpayer_class_code": "BUSINESS",
            "version_number": 1,
            "status": "active",
            "effective_from": "2026-01-01",
            "rule_definition_hash": "hash-002",
        },
    )
    bundle_id = bundle_response.json()["id"]

    unauthorized_list = await client.get("/tax/v1/rule-bundles", headers=CitizenHeaders.value())
    assert unauthorized_list.status_code == 403

    audit_response = await client.get(f"/tax/v1/calculations/{bundle_id}/audit-events", headers=CitizenHeaders.value())
    assert audit_response.status_code == 403


@pytest.mark.asyncio
async def test_missing_rule_bundle_returns_controlled_error(client: AsyncClient):
    response = await client.post(
        "/tax/v1/calculations",
        headers=CitizenHeaders.value("citizen-009"),
        json={
            "taxpayer_subject": "citizen-009",
            "jurisdiction_code": "NP",
            "tax_category_code": "PERSONAL_INCOME",
            "taxpayer_class_code": "RESIDENT",
            "assessment_date": "2026-06-21",
            "gross_income": 100000,
        },
    )
    assert response.status_code == 404
    assert response.json()["error_code"] == "TAX-4001"
