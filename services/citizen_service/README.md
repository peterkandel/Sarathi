# Citizen Service

FastAPI service for citizen profiles, citizenship records, and document metadata.

## Scope

The service integrates with Identity Service through the shared auth middleware and uses the authenticated principal subject as the citizen identity link.

## Core APIs

- `/api/v1/profiles`
- `/api/v1/profiles/me`
- `/api/v1/profiles/{profile_id}`
- `/api/v1/profiles/{profile_id}/citizenship-records`
- `/api/v1/citizenship-records/{record_id}`
- `/api/v1/profiles/{profile_id}/documents`
- `/api/v1/documents/{document_id}`

## Local Development

The service creates its schema on startup and is compatible with the shared `x-sarathi-*` development headers used by the auth middleware.
