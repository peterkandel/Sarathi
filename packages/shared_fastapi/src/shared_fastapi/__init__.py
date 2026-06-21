from .application.auth import build_principal, decode_access_token, get_current_principal_dependency
from .application.exceptions import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ConfigurationError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from .application.rbac import has_permission, has_role, require_permissions, require_roles
from .domain.events import DomainEvent, EventEnvelope, EventMetadata, IntegrationEvent
from .domain.security import Principal, TokenClaims
from .infrastructure.config import AppSettings, AuthSettings, DatabaseSettings, LoggingSettings, get_settings
from .infrastructure.database import Base, create_async_engine, create_session_factory, ensure_database_ready, session_scope
from .infrastructure.logging import configure_logging, get_logger, set_request_context
from .interfaces.http.errors import register_exception_handlers
from .interfaces.http.responses import APIErrorResponse, APIResponse, PaginationMeta, PaginatedResponse, ResponseMeta

__all__ = [
    "APIErrorResponse",
    "APIResponse",
    "AppSettings",
    "ApplicationError",
    "AuthenticationError",
    "AuthorizationError",
    "AuthSettings",
    "Base",
    "ConflictError",
    "ConfigurationError",
    "DatabaseSettings",
    "DomainEvent",
    "EventEnvelope",
    "EventMetadata",
    "ExternalServiceError",
    "IntegrationEvent",
    "LoggingSettings",
    "NotFoundError",
    "PaginationMeta",
    "PaginatedResponse",
    "Principal",
    "ResponseMeta",
    "TokenClaims",
    "ValidationError",
    "build_principal",
    "configure_logging",
    "create_async_engine",
    "create_session_factory",
    "decode_access_token",
    "ensure_database_ready",
    "get_current_principal_dependency",
    "get_logger",
    "get_settings",
    "has_permission",
    "has_role",
    "register_exception_handlers",
    "require_permissions",
    "require_roles",
    "session_scope",
    "set_request_context",
]
