# API Gateway

FastAPI BFF and ingress boundary for the SARATHI platform.

## Responsibilities
- Citizen-facing backend-for-frontend endpoints
- Routing to internal services
- AuthN/AuthZ enforcement
- Request validation and idempotency checks
- Response shaping for the mobile client

## Run
```bash
uvicorn app.main:app --reload --port 8000
```
