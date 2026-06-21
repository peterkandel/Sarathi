# Integration Service

FastAPI service for external API adapters, retries, circuit breakers, event publishing, and integration error handling.

## Architecture

The service acts as an anti-corruption layer for cross-agency communication. It normalizes external systems into canonical requests, persists adapter execution state, tracks circuit breaker health, and publishes integration events through a dedicated outbox table.

## Supported Systems

- Citizenship Registry
- Tax Authority
- Passport Systems
- Payment Systems

## API

- `POST /integration/v1/adapters`
- `GET /integration/v1/adapters`
- `GET /integration/v1/adapters/{adapter_id}`
- `POST /integration/v1/requests`
- `GET /integration/v1/requests`
- `GET /integration/v1/requests/{request_id}`
- `POST /integration/v1/requests/{request_id}/process`
- `GET /integration/v1/requests/{request_id}/attempts`
- `GET /integration/v1/requests/{request_id}/events`
- `GET /integration/v1/breakers`
- `POST /integration/v1/queue/process`
- `POST /integration/v1/events/publish`

## Notes

- Retry behavior is policy-driven with bounded attempts.
- Circuit breakers are persisted per adapter.
- Event publishing is handled through a pending event table so downstream consumers can replay safely.
