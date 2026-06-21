# Repository Layout

```text
/apps
  /mobile
  /citizen-portal
  /admin-portal
  /api_gateway
/services
  /identity_service
  /ocr_service
  /tax_service
  /workflow_service
  /notification_service
/packages
  /shared_types
  /shared_auth
  /shared_events
/infrastructure
  /docker
  /terraform
  /kubernetes
/docs
/ci_cd
```

## Layering Rules
- `apps/*` contains client-facing applications and the edge gateway.
- `services/*` contains backend domain services.
- `packages/*` contains shared contracts and utilities.
- `infrastructure/*` contains deployment and runtime assets.
- `docs/*` contains repository guidance and architecture source-of-truth documents.
- `ci_cd/*` contains pipeline documentation and reusable delivery guidance.
