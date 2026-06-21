from __future__ import annotations

from collections.abc import Callable, Iterable

from fastapi import Depends

from ..application.exceptions import AuthorizationError
from ..domain.security import Principal


def has_role(principal: Principal, *roles: str) -> bool:
    required_roles = set(roles)
    return bool(required_roles.intersection(principal.roles))


def has_permission(principal: Principal, *permissions: str) -> bool:
    required_permissions = set(permissions)
    return bool(required_permissions.intersection(principal.permissions))


def require_roles(*roles: str, principal_dependency: Callable[..., Principal]) -> Callable[..., Principal]:
    async def dependency(principal: Principal = Depends(principal_dependency)) -> Principal:
        if not has_role(principal, *roles):
            raise AuthorizationError("Missing required role")
        return principal

    return dependency


def require_permissions(*permissions: str, principal_dependency: Callable[..., Principal]) -> Callable[..., Principal]:
    async def dependency(principal: Principal = Depends(principal_dependency)) -> Principal:
        if not has_permission(principal, *permissions):
            raise AuthorizationError("Missing required permission")
        return principal

    return dependency


def any_of(values: Iterable[str], candidates: Iterable[str]) -> bool:
    return bool(set(values).intersection(candidates))
