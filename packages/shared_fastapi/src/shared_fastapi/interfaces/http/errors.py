from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ...application.exceptions import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from .responses import APIErrorBody, APIErrorResponse


def _build_error_response(message: str, code: str, status_code: int, *, details: dict[str, Any] | None = None) -> JSONResponse:
    payload = APIErrorResponse(error=APIErrorBody(code=code, message=message, details=details or {}))
    return JSONResponse(status_code=status_code, content=payload.model_dump())


async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    return _build_error_response(exc.message, exc.code, exc.status_code, details=exc.details)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _build_error_response("Request validation failed", "validation_error", 422, details={"errors": exc.errors()})


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _build_error_response(str(exc.detail), "http_exception", exc.status_code)


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return _build_error_response("Unexpected server error", "internal_server_error", 500)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(AuthenticationError, application_error_handler)
    app.add_exception_handler(AuthorizationError, application_error_handler)
    app.add_exception_handler(ValidationError, application_error_handler)
    app.add_exception_handler(NotFoundError, application_error_handler)
    app.add_exception_handler(ConflictError, application_error_handler)
    app.add_exception_handler(ExternalServiceError, application_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
