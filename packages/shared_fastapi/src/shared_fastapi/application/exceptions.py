from __future__ import annotations

from typing import Any


class ApplicationError(Exception):
    status_code = 500
    code = "application_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


class ConfigurationError(ApplicationError):
    status_code = 500
    code = "configuration_error"


class AuthenticationError(ApplicationError):
    status_code = 401
    code = "authentication_error"


class AuthorizationError(ApplicationError):
    status_code = 403
    code = "authorization_error"


class ValidationError(ApplicationError):
    status_code = 400
    code = "validation_error"


class NotFoundError(ApplicationError):
    status_code = 404
    code = "not_found_error"


class ConflictError(ApplicationError):
    status_code = 409
    code = "conflict_error"


class ExternalServiceError(ApplicationError):
    status_code = 502
    code = "external_service_error"
