# Environment Variable Strategy

## Principles
- Use `.env.example` as the canonical non-secret template.
- Keep secrets out of version control.
- Prefer one shared naming scheme across all apps and services.
- Use service-specific prefixes where collision risk exists.
- Separate public client variables from server-only variables.

## Naming Pattern
- Shared platform settings: `SARATHI_*`
- Service-specific settings: `<SERVICE>_*`
- Public web settings: `NEXT_PUBLIC_*`
- Sensitive backend settings: `*_SECRET`, `*_PASSWORD`, `*_TOKEN`, `*_KEY`

## Variable Sources
1. `.env.example` for documentation and onboarding.
2. Local `.env` for developer overrides.
3. CI/CD secrets for pipeline and deployment values.
4. Secret manager or vault for production values.

## Examples
- `DATABASE_URL`
- `REDIS_URL`
- `OBJECT_STORAGE_ENDPOINT`
- `JWT_ISSUER`
- `JWT_AUDIENCE`
- `SERVICE_NAME`
- `SERVICE_PORT`
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_SUPPORT_EMAIL`

## Rules
- Do not reuse the same variable name for different meanings.
- Do not expose backend secrets to the browser or mobile client.
- Keep environment configuration deterministic per deployment target.
- Use typed settings models in FastAPI services and validated config in Next.js apps.
