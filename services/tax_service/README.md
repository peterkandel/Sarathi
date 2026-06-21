# Tax Service

FastAPI service for configurable tax rules, bracket calculation, deductions, exemptions, explanation traces, and audit logging.

## Architecture

Tax rules are database-driven and organized into versioned rule bundles with child tables for brackets, deductions, and exemptions. The calculation engine resolves an applicable bundle by jurisdiction, category, taxpayer class, and assessment date, then evaluates exemptions, deductions, and progressive brackets in a deterministic order.

## API

- `POST /tax/v1/rule-bundles`
- `GET /tax/v1/rule-bundles`
- `GET /tax/v1/rule-bundles/{bundle_id}`
- `POST /tax/v1/rule-bundles/{bundle_id}/brackets`
- `POST /tax/v1/rule-bundles/{bundle_id}/deductions`
- `POST /tax/v1/rule-bundles/{bundle_id}/exemptions`
- `POST /tax/v1/calculations`
- `GET /tax/v1/calculations/{calculation_id}`
- `GET /tax/v1/calculations`
- `GET /tax/v1/calculations/{calculation_id}/audit-events`

## Notes

- Rule bundles are versioned and effective-dated.
- Audit logs are stored in a dedicated table and written for bundle creation and tax calculations.
- The calculation service is isolated behind repository and service interfaces so the rule engine can be replaced later without rewriting the API layer.
