# Tax Engine Design

## Scope
```json
{
  "name": "Configurable Tax Engine",
  "purpose": "Compute tax estimates from versioned legal rules without hardcoding tax logic.",
  "scope": [
    "Progressive tax brackets",
    "Deduction rules",
    "Exemptions",
    "Future legal updates",
    "Auditability",
    "Explainable calculations"
  ],
  "non_goals": [
    "Authoritative tax assessment",
    "Treasury payment processing",
    "Manual legal drafting of tax law inside code",
    "One-off hardcoded formulas for individual jurisdictions"
  ]
}
```

## 1. Rule Architecture
```json
{
  "architecture_style": "Policy-driven rules engine with versioned tax rule bundles",
  "principles": [
    "All tax logic is externalized into data-driven rule definitions",
    "Rule bundles are versioned and effective-dated",
    "Calculations are explainable line by line",
    "Legal updates are published as new rule versions, not code changes",
    "Jurisdiction, taxpayer class, and tax category determine the applicable rule bundle",
    "Deterministic rules execute before any optional recommendation or advisory logic"
  ],
  "core_modules": [
    {
      "name": "Rule Registry",
      "responsibility": "Stores versioned rule bundles, effective dates, and approval metadata."
    },
    {
      "name": "Eligibility Resolver",
      "responsibility": "Selects the correct rule bundle using jurisdiction, tax category, taxpayer type, and effective date."
    },
    {
      "name": "Computation Engine",
      "responsibility": "Applies brackets, deductions, exemptions, and caps in a deterministic order."
    },
    {
      "name": "Explanation Builder",
      "responsibility": "Produces an auditable calculation trace with human-readable breakdowns."
    },
    {
      "name": "Validation Layer",
      "responsibility": "Checks inputs, rule applicability, and output sanity before publishing a result."
    },
    {
      "name": "Legal Change Manager",
      "responsibility": "Activates future rule versions by effective date and records supersession history."
    },
    {
      "name": "Audit Publisher",
      "responsibility": "Writes immutable calculation and rule-selection events to the audit trail."
    }
  ],
  "calculation_order": [
    "Validate input payload",
    "Resolve applicable rule bundle",
    "Apply gross income or base amount normalization",
    "Apply exemptions",
    "Apply deductions",
    "Apply progressive bracket calculation",
    "Apply credits or offsets if the law allows",
    "Apply caps, floors, and rounding rules",
    "Generate explanation trace",
    "Persist calculation snapshot and publish audit events"
  ],
  "rule_types": [
    "progressive_bracket",
    "flat_rate",
    "deduction",
    "exemption",
    "credit",
    "offset",
    "cap",
    "rounding",
    "threshold",
    "eligibility_filter"
  ]
}
```

### Rule Evaluation Model
```json
{
  "evaluation_model": {
    "inputs": [
      "taxpayer profile",
      "jurisdiction",
      "tax category",
      "assessment date",
      "income and expense inputs",
      "declared exemptions",
      "declared deductions"
    ],
    "outputs": [
      "tax amount",
      "effective tax rate",
      "rule version used",
      "calculation trace",
      "validation warnings",
      "audit identifiers"
    ],
    "determinism": "The same inputs and same rule version must always produce the same output.",
    "fallback_behavior": "If a rule bundle is ambiguous or not found, the engine returns a controlled error and does not infer tax logic."
  }
}
```

## 2. Database Schema
```json
{
  "schema_name": "tax_engine",
  "design_constraints": {
    "primary_keys": "UUID",
    "naming": "snake_case",
    "audit_fields": ["created_at", "updated_at", "deleted_at", "created_by_actor_id", "updated_by_actor_id"],
    "soft_delete": "deleted_at",
    "multi_agency": "agency_id on agency-owned entities",
    "versioning": "effective-dated rule bundles with immutable published versions"
  },
  "tables": [
    {
      "name": "tax_engine.tax_rule_bundles",
      "purpose": "Top-level versioned rule container for a jurisdiction and tax category.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "agency_id", "type": "uuid", "constraints": ["not null", "fk reference_policy.agencies.id"]},
        {"name": "tax_category_id", "type": "uuid", "constraints": ["not null", "fk reference_policy.tax_categories.id"]},
        {"name": "rule_bundle_code", "type": "text", "constraints": ["not null"]},
        {"name": "rule_bundle_name", "type": "text", "constraints": ["not null"]},
        {"name": "jurisdiction_code", "type": "text", "constraints": ["not null"]},
        {"name": "taxpayer_class_code", "type": "text", "constraints": ["not null"]},
        {"name": "version_number", "type": "integer", "constraints": ["not null", "check version_number > 0"]},
        {"name": "status", "type": "text", "constraints": ["not null", "check status in ('draft','approved','active','retired')"]},
        {"name": "effective_from", "type": "date", "constraints": ["not null"]},
        {"name": "effective_to", "type": "date", "constraints": ["null"]},
        {"name": "approval_reference", "type": "text", "constraints": ["null"]},
        {"name": "rule_definition_hash", "type": "text", "constraints": ["not null"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": [
        "unique active(rule_bundle_code, version_number)",
        "unique active(agency_id, tax_category_id, jurisdiction_code, taxpayer_class_code, version_number)",
        "check effective_to is null or effective_to >= effective_from"
      ],
      "indexes": [
        "ix_tax_rule_bundles_agency_id",
        "ix_tax_rule_bundles_tax_category_id",
        "ix_tax_rule_bundles_status",
        "uq_tax_rule_bundles_active"
      ],
      "relationships": [
        "Parent table for rule components, brackets, deductions, exemptions, and legal update records."
      ]
    },
    {
      "name": "tax_engine.tax_rule_components",
      "purpose": "Stores the ordered rule components belonging to a rule bundle.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "tax_rule_bundle_id", "type": "uuid", "constraints": ["not null", "fk tax_rule_bundles.id"]},
        {"name": "component_type", "type": "text", "constraints": ["not null", "check component_type in ('progressive_bracket','deduction','exemption','credit','offset','cap','rounding','threshold','eligibility_filter')"]},
        {"name": "component_code", "type": "text", "constraints": ["not null"]},
        {"name": "component_name", "type": "text", "constraints": ["not null"]},
        {"name": "sequence_no", "type": "integer", "constraints": ["not null", "check sequence_no > 0"]},
        {"name": "applies_to", "type": "jsonb", "constraints": ["not null"]},
        {"name": "configuration", "type": "jsonb", "constraints": ["not null"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": [
        "unique active(tax_rule_bundle_id, component_code)",
        "unique active(tax_rule_bundle_id, sequence_no)",
        "foreign key to tax_rule_bundles"
      ],
      "indexes": [
        "ix_tax_rule_components_tax_rule_bundle_id",
        "ix_tax_rule_components_component_type"
      ],
      "relationships": [
        "Many components belong to one rule bundle."
      ]
    },
    {
      "name": "tax_engine.tax_brackets",
      "purpose": "Stores progressive tax bracket definitions.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "tax_rule_bundle_id", "type": "uuid", "constraints": ["not null", "fk tax_rule_bundles.id"]},
        {"name": "bracket_order", "type": "integer", "constraints": ["not null", "check bracket_order > 0"]},
        {"name": "lower_bound", "type": "numeric(18,2)", "constraints": ["not null", "check lower_bound >= 0"]},
        {"name": "upper_bound", "type": "numeric(18,2)", "constraints": ["null"]},
        {"name": "marginal_rate", "type": "numeric(7,6)", "constraints": ["not null", "check marginal_rate >= 0"]},
        {"name": "base_tax", "type": "numeric(18,2)", "constraints": ["not null", "default 0"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": [
        "unique active(tax_rule_bundle_id, bracket_order)",
        "check upper_bound is null or upper_bound > lower_bound",
        "check marginal_rate <= 1"
      ],
      "indexes": [
        "ix_tax_brackets_tax_rule_bundle_id",
        "uq_tax_brackets_active"
      ],
      "relationships": [
        "Many brackets belong to one rule bundle."
      ]
    },
    {
      "name": "tax_engine.tax_deductions",
      "purpose": "Stores configurable deduction rules.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "tax_rule_bundle_id", "type": "uuid", "constraints": ["not null", "fk tax_rule_bundles.id"]},
        {"name": "deduction_code", "type": "text", "constraints": ["not null"]},
        {"name": "deduction_name", "type": "text", "constraints": ["not null"]},
        {"name": "deduction_type", "type": "text", "constraints": ["not null", "check deduction_type in ('fixed_amount','percentage','capped_percentage','formula')"]},
        {"name": "calculation_basis", "type": "text", "constraints": ["not null"]},
        {"name": "configuration", "type": "jsonb", "constraints": ["not null"]},
        {"name": "priority_order", "type": "integer", "constraints": ["not null", "default 0"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": [
        "unique active(tax_rule_bundle_id, deduction_code)",
        "check priority_order >= 0"
      ],
      "indexes": [
        "ix_tax_deductions_tax_rule_bundle_id",
        "ix_tax_deductions_deduction_type"
      ],
      "relationships": [
        "Many deductions belong to one rule bundle."
      ]
    },
    {
      "name": "tax_engine.tax_exemptions",
      "purpose": "Stores exemption rules and eligibility conditions.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "tax_rule_bundle_id", "type": "uuid", "constraints": ["not null", "fk tax_rule_bundles.id"]},
        {"name": "exemption_code", "type": "text", "constraints": ["not null"]},
        {"name": "exemption_name", "type": "text", "constraints": ["not null"]},
        {"name": "exemption_type", "type": "text", "constraints": ["not null", "check exemption_type in ('full','partial','threshold','category_based')"]},
        {"name": "configuration", "type": "jsonb", "constraints": ["not null"]},
        {"name": "priority_order", "type": "integer", "constraints": ["not null", "default 0"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": [
        "unique active(tax_rule_bundle_id, exemption_code)",
        "check priority_order >= 0"
      ],
      "indexes": [
        "ix_tax_exemptions_tax_rule_bundle_id",
        "ix_tax_exemptions_exemption_type"
      ],
      "relationships": [
        "Many exemptions belong to one rule bundle."
      ]
    },
    {
      "name": "tax_engine.tax_legal_updates",
      "purpose": "Records future legal updates and scheduled activation of new rule bundles.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "agency_id", "type": "uuid", "constraints": ["not null", "fk reference_policy.agencies.id"]},
        {"name": "tax_rule_bundle_id", "type": "uuid", "constraints": ["not null", "fk tax_rule_bundles.id"]},
        {"name": "legal_update_code", "type": "text", "constraints": ["not null"]},
        {"name": "update_type", "type": "text", "constraints": ["not null", "check update_type in ('new_rule','amendment','retirement','effective_date_change')"]},
        {"name": "published_at", "type": "timestamptz", "constraints": ["not null"]},
        {"name": "effective_from", "type": "date", "constraints": ["not null"]},
        {"name": "summary", "type": "text", "constraints": ["not null"]},
        {"name": "source_reference", "type": "text", "constraints": ["null"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": [
        "unique active(legal_update_code)",
        "check effective_from >= date(published_at)",
        "future-dated changes must not replace active rules until effective_from"
      ],
      "indexes": [
        "ix_tax_legal_updates_agency_id",
        "ix_tax_legal_updates_effective_from",
        "ix_tax_legal_updates_tax_rule_bundle_id"
      ],
      "relationships": [
        "Many legal updates may point to one rule bundle."
      ]
    },
    {
      "name": "tax_engine.tax_calculation_requests",
      "purpose": "Stores every incoming calculation request.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "agency_id", "type": "uuid", "constraints": ["not null", "fk reference_policy.agencies.id"]},
        {"name": "citizen_profile_id", "type": "uuid", "constraints": ["not null"]},
        {"name": "tax_category_id", "type": "uuid", "constraints": ["not null"]},
        {"name": "request_payload", "type": "jsonb", "constraints": ["not null"]},
        {"name": "request_status", "type": "text", "constraints": ["not null", "check request_status in ('received','validated','calculated','failed')"]},
        {"name": "requested_at", "type": "timestamptz", "constraints": ["not null"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": [
        "request payload must include the declared income base and requested tax year",
        "unique active(id)"
      ],
      "indexes": [
        "ix_tax_calculation_requests_agency_id",
        "ix_tax_calculation_requests_citizen_profile_id",
        "ix_tax_calculation_requests_requested_at"
      ],
      "relationships": [
        "Parent record for one or more calculation results."
      ]
    },
    {
      "name": "tax_engine.tax_calculation_results",
      "purpose": "Stores final computed values and explanations.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "tax_calculation_request_id", "type": "uuid", "constraints": ["not null", "fk tax_calculation_requests.id"]},
        {"name": "tax_rule_bundle_id", "type": "uuid", "constraints": ["not null", "fk tax_rule_bundles.id"]},
        {"name": "gross_income", "type": "numeric(18,2)", "constraints": ["not null", "check gross_income >= 0"]},
        {"name": "taxable_income", "type": "numeric(18,2)", "constraints": ["not null", "check taxable_income >= 0"]},
        {"name": "total_exemptions", "type": "numeric(18,2)", "constraints": ["not null", "default 0"]},
        {"name": "total_deductions", "type": "numeric(18,2)", "constraints": ["not null", "default 0"]},
        {"name": "pre_credit_tax", "type": "numeric(18,2)", "constraints": ["not null", "default 0"]},
        {"name": "total_credits", "type": "numeric(18,2)", "constraints": ["not null", "default 0"]},
        {"name": "final_tax_amount", "type": "numeric(18,2)", "constraints": ["not null", "check final_tax_amount >= 0"]},
        {"name": "effective_tax_rate", "type": "numeric(7,6)", "constraints": ["not null", "check effective_tax_rate >= 0"]},
        {"name": "rounding_mode", "type": "text", "constraints": ["not null"]},
        {"name": "calculation_trace", "type": "jsonb", "constraints": ["not null"]},
        {"name": "calculated_at", "type": "timestamptz", "constraints": ["not null"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": [
        "one calculation result per accepted request version",
        "calculation_trace must be immutable once published"
      ],
      "indexes": [
        "ix_tax_calculation_results_tax_calculation_request_id",
        "ix_tax_calculation_results_tax_rule_bundle_id",
        "ix_tax_calculation_results_calculated_at"
      ],
      "relationships": [
        "Each request may have one or more results over time, but only the latest published result is active."
      ]
    },
    {
      "name": "tax_engine.tax_calculation_line_items",
      "purpose": "Stores explainable line items for the final tax calculation.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "tax_calculation_result_id", "type": "uuid", "constraints": ["not null", "fk tax_calculation_results.id"]},
        {"name": "line_type", "type": "text", "constraints": ["not null", "check line_type in ('base','exemption','deduction','bracket','credit','rounding','adjustment')"]},
        {"name": "line_code", "type": "text", "constraints": ["not null"]},
        {"name": "line_label", "type": "text", "constraints": ["not null"]},
        {"name": "base_amount", "type": "numeric(18,2)", "constraints": ["not null", "default 0"]},
        {"name": "rate", "type": "numeric(7,6)", "constraints": ["null"]},
        {"name": "line_amount", "type": "numeric(18,2)", "constraints": ["not null"]},
        {"name": "formula_text", "type": "text", "constraints": ["not null"]},
        {"name": "sort_order", "type": "integer", "constraints": ["not null", "default 0"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": [
        "unique active(tax_calculation_result_id, line_code)",
        "line_amount may be positive or negative depending on line_type"
      ],
      "indexes": [
        "ix_tax_calculation_line_items_tax_calculation_result_id",
        "ix_tax_calculation_line_items_line_type",
        "ix_tax_calculation_line_items_sort_order"
      ],
      "relationships": [
        "Many line items belong to one calculation result."
      ]
    },
    {
      "name": "tax_engine.tax_audit_events",
      "purpose": "Stores immutable audit records for tax rule changes and calculations.",
      "columns": [
        {"name": "id", "type": "uuid", "constraints": ["primary key", "default gen_random_uuid()"]},
        {"name": "agency_id", "type": "uuid", "constraints": ["not null", "fk reference_policy.agencies.id"]},
        {"name": "event_type", "type": "text", "constraints": ["not null"]},
        {"name": "entity_type", "type": "text", "constraints": ["not null"]},
        {"name": "entity_id", "type": "uuid", "constraints": ["not null"]},
        {"name": "actor_type", "type": "text", "constraints": ["not null", "check actor_type in ('citizen','staff','system','agency')"]},
        {"name": "actor_reference", "type": "text", "constraints": ["null"]},
        {"name": "correlation_id", "type": "uuid", "constraints": ["null"]},
        {"name": "event_payload", "type": "jsonb", "constraints": ["not null"]},
        {"name": "event_at", "type": "timestamptz", "constraints": ["not null"]},
        {"name": "created_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "updated_at", "type": "timestamptz", "constraints": ["not null", "default now()"]},
        {"name": "deleted_at", "type": "timestamptz", "constraints": ["null"]},
        {"name": "created_by_actor_id", "type": "uuid", "constraints": ["null"]},
        {"name": "updated_by_actor_id", "type": "uuid", "constraints": ["null"]}
      ],
      "constraints": [
        "append-only semantics for published events",
        "tax rule bundle and result events must preserve exact rule version references"
      ],
      "indexes": [
        "ix_tax_audit_events_agency_id",
        "ix_tax_audit_events_entity",
        "ix_tax_audit_events_event_at",
        "ix_tax_audit_events_correlation_id"
      ],
      "relationships": [
        "References any tax engine entity by logical UUID."
      ]
    }
  ]
}
```

## 3. Calculation Engine
```json
{
  "engine_style": "Deterministic rule interpreter",
  "execution_contract": {
    "inputs": [
      "citizen profile",
      "jurisdiction",
      "tax category",
      "tax year",
      "gross income or tax base",
      "declared deductions",
      "declared exemptions",
      "effective date"
    ],
    "outputs": [
      "final tax amount",
      "line item breakdown",
      "effective tax rate",
      "rule bundle version",
      "validation warnings",
      "audit identifiers"
    ]
  },
  "execution_steps": [
    {
      "step": 1,
      "name": "Input validation",
      "details": "Validate numeric ranges, required fields, tax year, jurisdiction, and tax category presence."
    },
    {
      "step": 2,
      "name": "Rule bundle resolution",
      "details": "Select the latest approved bundle whose effective date covers the calculation date."
    },
    {
      "step": 3,
      "name": "Exemption application",
      "details": "Apply full or partial exemptions before deductions when the law specifies that ordering."
    },
    {
      "step": 4,
      "name": "Deduction application",
      "details": "Apply deduction rules in configured priority order and honor caps, floors, and eligibility filters."
    },
    {
      "step": 5,
      "name": "Progressive bracket calculation",
      "details": "Allocate taxable income across bracket ranges and compute tax per bracket."
    },
    {
      "step": 6,
      "name": "Credit and offset application",
      "details": "Apply refundable or non-refundable credits as defined by the configured rule bundle."
    },
    {
      "step": 7,
      "name": "Rounding and finalization",
      "details": "Apply configured rounding rules and compute the final payable amount."
    },
    {
      "step": 8,
      "name": "Trace generation",
      "details": "Produce an explainable calculation trace and persist line items."
    }
  ],
  "rule_evaluation_order": [
    "Eligibility filters",
    "Exemptions",
    "Deductions",
    "Bracket taxation",
    "Credits",
    "Offsets",
    "Rounding",
    "Post-calculation validation"
  ],
  "key_controls": [
    "Reject ambiguous rule bundle selection",
    "Disallow negative taxable income unless the rule explicitly allows it",
    "Separate rule lookup from calculation execution",
    "Persist exact rule bundle and component IDs in the trace",
    "Version every calculation result"
  ]
}
```

### Bracket Algorithm
```json
{
  "progressive_bracket_algorithm": {
    "formula": "tax = base_tax_for_bracket + (taxable_income - lower_bound) * marginal_rate",
    "processing": [
      "Sort brackets by lower_bound ascending",
      "Choose the highest bracket where taxable_income >= lower_bound",
      "If upper_bound exists, ensure taxable_income <= upper_bound for bracket allocation",
      "Compute bracket tax using the configured base_tax and marginal_rate",
      "Sum bracket outputs if the law uses segmented ranges"
    ],
    "guardrails": [
      "Do not hardcode bracket limits in code",
      "Require configuration validation to prevent overlapping brackets",
      "Validate monotonic bracket order",
      "Reject gaps unless the rule bundle explicitly allows them"
    ]
  }
}
```

## 4. API Contracts
```json
{
  "api_version": "v1",
  "base_path": "/tax-engine/v1",
  "authentication": {
    "user": "Bearer JWT",
    "service": "mTLS plus service token"
  },
  "endpoints": [
    {
      "method": "POST",
      "path": "/calculations",
      "purpose": "Create a tax calculation request and execute the engine.",
      "authorization": ["citizen access", "tax officer access", "system-to-system access"],
      "request_schema": {
        "type": "object",
        "required": ["tax_category_code", "jurisdiction_code", "taxpayer_class_code", "tax_year", "gross_amount"],
        "properties": {
          "tax_category_code": {"type": "string"},
          "jurisdiction_code": {"type": "string"},
          "taxpayer_class_code": {"type": "string"},
          "tax_year": {"type": "integer"},
          "gross_amount": {"type": "number"},
          "deductions": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["deduction_code", "amount"],
              "properties": {
                "deduction_code": {"type": "string"},
                "amount": {"type": "number"},
                "metadata": {"type": "object"}
              }
            }
          },
          "exemptions": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["exemption_code"],
              "properties": {
                "exemption_code": {"type": "string"},
                "metadata": {"type": "object"}
              }
            }
          },
          "calculation_date": {"type": "string", "format": "date"}
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["calculation_id", "rule_bundle_version", "final_tax_amount", "effective_tax_rate", "line_items"],
        "properties": {
          "calculation_id": {"type": "string", "format": "uuid"},
          "rule_bundle_id": {"type": "string", "format": "uuid"},
          "rule_bundle_version": {"type": "integer"},
          "final_tax_amount": {"type": "number"},
          "effective_tax_rate": {"type": "number"},
          "line_items": {
            "type": "array",
            "items": {"type": "object"}
          },
          "validation_status": {"type": "string", "enum": ["passed", "passed_with_warnings", "failed"]},
          "warnings": {"type": "array", "items": {"type": "object"}}
        }
      },
      "error_responses": [400, 401, 403, 404, 409, 422]
    },
    {
      "method": "GET",
      "path": "/calculations/{calculation_id}",
      "purpose": "Retrieve a previously executed calculation.",
      "authorization": ["citizen access to own calculation", "tax officer access", "audit access"],
      "request_schema": {
        "type": "object",
        "properties": {
          "calculation_id": {"type": "string", "format": "uuid"}
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["calculation_id", "final_tax_amount", "line_items"],
        "properties": {
          "calculation_id": {"type": "string", "format": "uuid"},
          "final_tax_amount": {"type": "number"},
          "effective_tax_rate": {"type": "number"},
          "rule_bundle_version": {"type": "integer"},
          "line_items": {"type": "array", "items": {"type": "object"}},
          "calculation_trace": {"type": "object"}
        }
      },
      "error_responses": [401, 403, 404]
    },
    {
      "method": "GET",
      "path": "/rule-bundles",
      "purpose": "List tax rule bundles with effective dates and versions.",
      "authorization": ["tax administrator access", "audit access"],
      "request_schema": {
        "type": "object",
        "properties": {
          "tax_category_code": {"type": "string"},
          "jurisdiction_code": {"type": "string"},
          "status": {"type": "string"}
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["items", "page"],
        "properties": {
          "items": {"type": "array", "items": {"type": "object"}},
          "page": {"type": "object"}
        }
      },
      "error_responses": [401, 403]
    },
    {
      "method": "POST",
      "path": "/rule-bundles",
      "purpose": "Create a draft tax rule bundle.",
      "authorization": ["tax administrator access"],
      "request_schema": {
        "type": "object",
        "required": ["tax_category_id", "jurisdiction_code", "taxpayer_class_code", "rule_bundle_name", "effective_from"],
        "properties": {
          "tax_category_id": {"type": "string", "format": "uuid"},
          "jurisdiction_code": {"type": "string"},
          "taxpayer_class_code": {"type": "string"},
          "rule_bundle_name": {"type": "string"},
          "effective_from": {"type": "string", "format": "date"},
          "components": {"type": "array", "items": {"type": "object"}}
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["rule_bundle_id", "status"],
        "properties": {
          "rule_bundle_id": {"type": "string", "format": "uuid"},
          "status": {"type": "string", "enum": ["draft", "approved", "active"]}
        }
      },
      "error_responses": [400, 401, 403, 422]
    },
    {
      "method": "POST",
      "path": "/rule-bundles/{rule_bundle_id}/activate",
      "purpose": "Activate an approved rule bundle for an effective date.",
      "authorization": ["tax administrator access"],
      "request_schema": {
        "type": "object",
        "properties": {
          "activation_reason": {"type": "string"}
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["rule_bundle_id", "status", "effective_from"],
        "properties": {
          "rule_bundle_id": {"type": "string", "format": "uuid"},
          "status": {"type": "string"},
          "effective_from": {"type": "string", "format": "date"}
        }
      },
      "error_responses": [401, 403, 404, 409]
    }
  ]
}
```

### Pagination Contract
```json
{
  "pagination": {
    "style": "limit-offset",
    "request_parameters": ["limit", "offset"],
    "response_envelope": {
      "items": [],
      "page": {
        "limit": 20,
        "offset": 0,
        "total": 0
      }
    },
    "recommended_limits": {
      "default": 20,
      "maximum": 100
    }
  }
}
```

## 5. Audit Strategy
```json
{
  "audit_strategy": {
    "objectives": [
      "Prove which rule version produced a result",
      "Reconstruct the exact calculation steps",
      "Track legal updates and activation history",
      "Support dispute resolution and oversight",
      "Detect unauthorized rule changes"
    ],
    "events": [
      "TaxRuleBundleCreated",
      "TaxRuleBundleApproved",
      "TaxRuleBundleActivated",
      "TaxRuleBundleRetired",
      "TaxCalculationRequested",
      "TaxCalculationValidated",
      "TaxCalculationCompleted",
      "TaxCalculationViewed",
      "TaxLegalUpdateRecorded",
      "TaxCalculationRejected"
    ],
    "audit_fields": [
      "request_id",
      "calculation_id",
      "rule_bundle_id",
      "rule_bundle_version",
      "actor_type",
      "actor_reference",
      "citizen_profile_id",
      "agency_id",
      "correlation_id",
      "event_at",
      "event_payload"
    ],
    "controls": [
      "Immutable audit trail for calculation requests and outputs",
      "Immutable trace of rule bundle changes",
      "Record approval and activation timestamps for legal updates",
      "Log both successful and failed calculations",
      "Retain formula trace and line items for dispute resolution",
      "Separate operational logs from compliance logs"
    ],
    "retention_policy": {
      "calculation_results": "per tax record retention law",
      "rule_bundles": "retain superseded versions according to legal archive policy",
      "audit_events": "retain according to oversight and records rules",
      "draft_rule_artifacts": "purge or archive after approval/rejection per policy"
    },
    "security_controls": [
      "Role-based access for tax administrators and auditors",
      "Tamper-evident event storage",
      "Checksum or hash of every published rule bundle",
      "Separation of duties between rule authors, approvers, and operators"
    ]
  }
}
```

## 6. Example Calculations
```json
{
  "examples": [
    {
      "example_name": "Progressive bracket with one deduction and one exemption",
      "inputs": {
        "gross_income": 1200000,
        "exemptions": [
          {"code": "EXEMPT_DISABILITY", "amount": 100000}
        ],
        "deductions": [
          {"code": "DED_NPS", "amount": 50000}
        ],
        "rule_bundle": "RB-2026-INCOME-001"
      },
      "calculation": {
        "taxable_income": 1200000 - 100000 - 50000,
        "brackets": [
          {"range": "0-500000", "rate": 0.01, "tax": 5000},
          {"range": "500001-1000000", "rate": 0.10, "tax": 50000},
          {"range": "1000001-1050000", "rate": 0.20, "tax": 10000}
        ],
        "final_tax_before_rounding": 65000,
        "final_tax_amount": 65000
      },
      "explanation": [
        "Start with gross income of 1,200,000.",
        "Subtract exemption of 100,000.",
        "Subtract deduction of 50,000.",
        "Apply progressive brackets to taxable income of 1,050,000.",
        "Sum bracket output to produce final tax amount of 65,000."
      ]
    },
    {
      "example_name": "Full exemption for eligible income category",
      "inputs": {
        "gross_income": 300000,
        "exemptions": [
          {"code": "EXEMPT_AGRICULTURE", "amount": 300000}
        ],
        "deductions": [],
        "rule_bundle": "RB-2026-AGRI-001"
      },
      "calculation": {
        "taxable_income": 0,
        "final_tax_before_rounding": 0,
        "final_tax_amount": 0
      },
      "explanation": [
        "Eligible income is fully exempt under the active rule bundle.",
        "No taxable income remains after exemption application.",
        "Final tax is zero."
      ]
    },
    {
      "example_name": "Percentage deduction with cap",
      "inputs": {
        "gross_income": 800000,
        "exemptions": [],
        "deductions": [
          {"code": "DED_CHARITY", "amount": 120000}
        ],
        "rule_bundle": "RB-2026-DED-002"
      },
      "calculation": {
        "deduction_rule": "10% of gross income capped at 60,000",
        "allowed_deduction": 60000,
        "taxable_income": 740000,
        "final_tax_amount": "computed by active brackets"
      },
      "explanation": [
        "The user declared 120,000 in charitable deductions.",
        "The active rule allows 10% of gross income with a cap of 60,000.",
        "Only 60,000 is allowed as a deduction.",
        "Taxable income becomes 740,000 before bracket calculation."
      ]
    },
    {
      "example_name": "Future legal update activation",
      "inputs": {
        "calculation_date": "2026-07-01",
        "published_at": "2026-06-15",
        "effective_from": "2026-07-01",
        "old_rule_bundle": "RB-2026-INCOME-001",
        "new_rule_bundle": "RB-2026-INCOME-002"
      },
      "calculation": {
        "rule_selection": "RB-2026-INCOME-002",
        "reason": "Effective date matches new legal update.",
        "result": "New bundle used without code change"
      },
      "explanation": [
        "The engine selects the bundle whose effective_from date matches the calculation date.",
        "The older bundle is not used once the new rule becomes effective.",
        "This allows future legal updates to be activated safely and predictably."
      ]
    }
  ]
}
```

## 7. Failure Modes
```json
{
  "failure_modes": [
    {
      "code": "TAX-001",
      "name": "rule_bundle_not_found",
      "severity": "high",
      "behavior": "Do not calculate; return a controlled error and require rule administration."
    },
    {
      "code": "TAX-002",
      "name": "conflicting_active_rules",
      "severity": "high",
      "behavior": "Reject calculation until the conflict is resolved."
    },
    {
      "code": "TAX-003",
      "name": "invalid_income_input",
      "severity": "medium",
      "behavior": "Return validation errors for out-of-range or malformed values."
    },
    {
      "code": "TAX-004",
      "name": "unsupported_deduction_code",
      "severity": "medium",
      "behavior": "Ignore unknown deductions only if policy allows; otherwise fail validation."
    },
    {
      "code": "TAX-005",
      "name": "legal_update_not_yet_effective",
      "severity": "medium",
      "behavior": "Use the active bundle as of the calculation date and log the decision."
    },
    {
      "code": "TAX-006",
      "name": "audit_publish_failure",
      "severity": "high",
      "behavior": "Mark calculation as pending publication or fail closed according to policy."
    }
  ],
  "resilience_policy": {
    "transient_failures": "Retry rule lookup, audit publication, and reference fetches with bounded backoff.",
    "permanent_failures": "Return deterministic errors and preserve the request payload for review.",
    "replay": "Allow safe re-execution of a request only when idempotency keys are present."
  }
}
```

## 8. Recommended Operating Model
```json
{
  "operating_model": {
    "rule_authoring": "Policy administrators author draft bundles and components.",
    "rule_approval": "Authorized tax/legal reviewers approve bundles before activation.",
    "rule_activation": "Activation occurs only on or after the configured effective_from date.",
    "calculation_execution": "The engine reads active bundles and never embeds legal formulas in code.",
    "change_management": "Every legal update creates a new bundle version, preserving prior versions for audit."
  }
}
```

## Summary
```json
{
  "summary": "This tax engine design externalizes all tax logic into versioned, effective-dated rules; supports progressive brackets, deductions, exemptions, and future legal updates; provides explainable calculations; and preserves a complete audit trail without hardcoding tax law.",
  "recommended_next_step": "Convert this design into a rule authoring specification and implementation backlog for the tax service."
}
```
