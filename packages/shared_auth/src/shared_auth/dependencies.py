from __future__ import annotations

from collections.abc import Callable, Iterable

from fastapi import HTTPException, Request, status

from .audit import AuditLogger, build_audit_event
from .config import AuthSettings
from .models import Permission, Principal, Role
from .security import has_any_role, has_permission, principal_from_request


def get_principal(request: Request) -> Principal:
    cached_principal = getattr(request.state, "principal", None)
    if cached_principal is not None:
        return cached_principal
    principal = principal_from_request(request, AuthSettings())
    request.state.principal = principal
    return principal


def require_role(*allowed_roles: Role) -> Callable[[Request], Principal]:
    def dependency(request: Request) -> Principal:
        principal = get_principal(request)
        if allowed_roles and not has_any_role(principal, allowed_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not permitted")
        return principal

    return dependency


def require_permission(permission: Permission) -> Callable[[Request], Principal]:
    def dependency(request: Request) -> Principal:
        principal = get_principal(request)
        if not has_permission(principal, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission not granted")
        return principal

    return dependency


def require_resource_access(
    *,
    resource_owner_id: str,
    resource_agency_id: str | None = None,
    elevated_roles: Iterable[Role] = (Role.CLERK, Role.REVIEWER, Role.MANAGER, Role.ADMINISTRATOR, Role.SUPER_ADMINISTRATOR),
) -> Callable[[Request], Principal]:
    def dependency(request: Request) -> Principal:
        principal = get_principal(request)
        owns_resource = principal.subject == resource_owner_id
        same_agency = resource_agency_id is not None and principal.agency_id == resource_agency_id
        elevated_access = has_any_role(principal, elevated_roles)
        if not (owns_resource or same_agency or elevated_access):
            AuditLogger().log(
                build_audit_event(
                    event_type="AuthorizationDenied",
                    action="resource_access",
                    outcome="denied",
                    principal=principal,
                    resource_type="resource",
                    resource_id=resource_owner_id,
                    details={"resource_agency_id": resource_agency_id},
                )
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Resource access denied")

        AuditLogger().log(
            build_audit_event(
                event_type="AuthorizationGranted",
                action="resource_access",
                outcome="allowed",
                principal=principal,
                resource_type="resource",
                resource_id=resource_owner_id,
                details={"resource_agency_id": resource_agency_id},
            )
        )
        return principal

    return dependency


def authorize_resource_access(
    request: Request,
    *,
    resource_owner_id: str,
    resource_agency_id: str | None = None,
    elevated_roles: Iterable[Role] = (Role.CLERK, Role.REVIEWER, Role.MANAGER, Role.ADMINISTRATOR, Role.SUPER_ADMINISTRATOR),
) -> Principal:
    principal = get_principal(request)
    owns_resource = principal.subject == resource_owner_id
    same_agency = resource_agency_id is not None and principal.agency_id == resource_agency_id
    elevated_access = has_any_role(principal, elevated_roles)
    if not (owns_resource or same_agency or elevated_access):
        AuditLogger().log(
            build_audit_event(
                event_type="AuthorizationDenied",
                action="resource_access",
                outcome="denied",
                principal=principal,
                resource_type="resource",
                resource_id=resource_owner_id,
                details={"resource_agency_id": resource_agency_id},
            )
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Resource access denied")

    AuditLogger().log(
        build_audit_event(
            event_type="AuthorizationGranted",
            action="resource_access",
            outcome="allowed",
            principal=principal,
            resource_type="resource",
            resource_id=resource_owner_id,
            details={"resource_agency_id": resource_agency_id},
        )
    )
    return principal