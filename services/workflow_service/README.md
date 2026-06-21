# Workflow Service

FastAPI service for configurable workflow orchestration, state machines, approval chains, and escalation rules.

## Scope

Workflow definitions are stored in database tables and extended through service APIs.

## Core APIs

- `/api/v1/definitions`
- `/api/v1/definitions/{definition_id}/states`
- `/api/v1/definitions/{definition_id}/transitions`
- `/api/v1/definitions/{definition_id}/approval-chains`
- `/api/v1/approval-chains/{chain_id}/steps`
- `/api/v1/definitions/{definition_id}/escalation-rules`
- `/api/v1/applications/submit`
- `/api/v1/applications/{application_id}/approve`
- `/api/v1/applications/{application_id}/reject`
- `/api/v1/applications/{application_id}/escalate`
