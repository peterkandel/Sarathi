# shared-fastapi

Shared FastAPI utilities for SARATHI backend services.

## Included layers

- `shared_fastapi.infrastructure`: configuration, database, and logging utilities
- `shared_fastapi.application`: authentication, RBAC, and application errors
- `shared_fastapi.interfaces.http`: HTTP response and exception adapters
- `shared_fastapi.domain`: cross-service domain models for security and events

## Typical usage

```python
from shared_fastapi import AppSettings, configure_logging, create_async_engine

settings = AppSettings()
configure_logging(settings.logging, service_name=settings.app_name)
engine = create_async_engine(settings.database)
```
