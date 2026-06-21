# Local Development

## Startup Command
Use one command to bring up the local platform:

```bash
docker compose up
```

## Services Started Locally
- PostgreSQL
- Redis
- API Gateway
- Identity Service
- Citizen Service

## Network Architecture
- `frontend` network: reserved for edge-facing or browser-facing services.
- `backend` network: shared network for data stores and backend services.
- Services resolve each other by Docker Compose service name on the backend network.
- The gateway can reach `identity_service` and `citizen_service` by DNS name without hardcoded IPs.

## Persistent Volumes
- `postgres_data` for PostgreSQL
- `redis_data` for Redis

## Service Discovery
- `postgres:5432`
- `redis:6379`
- `api_gateway:8000`
- `identity_service:8001`
- `citizen_service:8002`

## Environment Variables
Copy `.env.example` to `.env` and adjust the following values when needed:
- `DATABASE_URL`
- `REDIS_URL`
- `API_GATEWAY_URL`
- `IDENTITY_SERVICE_URL`
- `CITIZEN_SERVICE_URL`

## Notes
- The local stack is designed so backend code can be developed without external dependencies.
- Business logic stays in services, not in the portals or gateway.