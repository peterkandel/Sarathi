from __future__ import annotations

from time import perf_counter

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .audit import AuditLogger, build_audit_event
from .config import AuthSettings
from .security import principal_from_request


class PrincipalMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: AuthSettings | None = None) -> None:
        super().__init__(app)
        self._settings = settings or AuthSettings()

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path == "/health":
            return await call_next(request)
        request.state.principal = principal_from_request(request, self._settings)
        return await call_next(request)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: AuthSettings | None = None) -> None:
        super().__init__(app)
        self._settings = settings or AuthSettings()
        self._audit_logger = AuditLogger()

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = perf_counter()
        principal = getattr(request.state, "principal", None)
        if principal is None and request.url.path != "/health":
            principal = principal_from_request(request, self._settings)
            request.state.principal = principal
        self._audit_logger.log(
            build_audit_event(
                event_type="RequestReceived",
                action=f"{request.method} {request.url.path}",
                outcome="started",
                principal=principal,
                details={"client_host": request.client.host if request.client else None},
            )
        )
        response = await call_next(request)
        elapsed_ms = round((perf_counter() - start_time) * 1000, 2)
        self._audit_logger.log(
            build_audit_event(
                event_type="RequestCompleted",
                action=f"{request.method} {request.url.path}",
                outcome=str(response.status_code),
                principal=principal,
                details={"duration_ms": elapsed_ms},
            )
        )
        return response