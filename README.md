# SARATHI Platform Monorepo

Production-grade monorepo for the SARATHI digital government platform.

## Architecture Alignment
This repository follows a platform-first architecture with three client surfaces over shared backend services:
- Citizen Mobile App
- Citizen Web Portal
- Government Administrative Portal
- Shared FastAPI backend services
- PostgreSQL for transactional persistence
- Redis for caching and coordination
- S3-compatible object storage for documents and artifacts
- Dedicated citizen and administrative API gateway layers
- Shared auth, event, and type packages
- Container-first local and production deployment model

## Repository Layout
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

## Top-Level Responsibilities
- `apps/mobile`: Citizen mobile application
- `apps/citizen-portal`: Citizen web portal
- `apps/admin-portal`: Government administrative portal
- `apps/api_gateway`: Citizen and administrative API boundary
- `services/identity_service`: identity, consent, and profile lookup
- `services/ocr_service`: OCR, extraction, validation, fraud scoring
- `services/tax_service`: tax guidance and configurable tax engine
- `services/workflow_service`: workflow orchestration engine
- `services/notification_service`: official notification inbox and delivery
- `packages/shared_types`: shared TypeScript types for client applications
- `packages/shared_auth`: shared Python auth helpers and policies
- `packages/shared_events`: shared Python event contracts and schemas

## Canonical Architecture
The source of truth for the platform architecture is [Platform_Architecture.md](Platform_Architecture.md).

Repository guidance lives in [docs](docs):
- [Repository layout](docs/repository-layout.md)
- [Development workflow](docs/development-workflow.md)
- [Naming conventions](docs/naming-conventions.md)
- [Environment variables](docs/environment-variables.md)

## Prerequisites
- Python 3.11+
- Node.js 20+
- pnpm 9+
- Docker Desktop or compatible container runtime
- Git

## Local Development
Start the full stack with Docker Compose:

```bash
docker compose up
```

The compose stack starts PostgreSQL, Redis, the API Gateway, the Identity Service, and the Citizen Service on a shared backend network with service-name DNS discovery.

## Recommended Commands
```bash
make up
make down
make logs
make lint-python
make lint-web
```

## Design Rules
- Keep business logic inside domain services, not the gateway.
- Keep external system translation inside the integration layer.
- Use versioned APIs.
- Use idempotent create and submit operations.
- Use append-only audit events for security-critical actions.
- Avoid shared databases across bounded contexts.

## Service Ports
- `apps/api_gateway`: 8000
- `services/identity_service`: 8001
- `services/ocr_service`: 8002
- `services/tax_service`: 8003
- `services/workflow_service`: 8004
- `services/notification_service`: 8005
- `postgres`: 5432
- `redis`: 6379
- `minio`: 9000 / 9001

## Next Steps
- Connect services to the shared event and auth packages.
- Replace stub endpoints with the cataloged APIs.
- Add automated tests and policy validation checks.
- Connect infrastructure/terraform and infrastructure/kubernetes to real deployment targets.
