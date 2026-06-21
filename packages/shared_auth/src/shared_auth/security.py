from __future__ import annotations

import base64
import json
from collections.abc import Iterable
from typing import Any

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt

from .config import AuthSettings
from .models import Permission, Principal, Role
from .policies import permissions_for_roles


def _normalize_header_list(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _principal_from_dev_headers(request: Request, settings: AuthSettings) -> Principal:
    subject = request.headers.get(settings.dev_subject_header)
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing development subject header")
    role_values = _normalize_header_list(request.headers.get(settings.dev_roles_header))
    roles = [Role(role_value) for role_value in role_values]
    permissions = sorted(permissions_for_roles(roles), key=lambda item: item.value)
    agency_id = request.headers.get(settings.dev_agency_header)
    return Principal(subject=subject, roles=roles, permissions=permissions, agency_id=agency_id)


def _decode_unverified_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token format")
    padded_payload = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        payload_bytes = base64.urlsafe_b64decode(padded_payload.encode("ascii"))
        return json.loads(payload_bytes)
    except (ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload") from error


def _principal_from_jwt(token: str, settings: AuthSettings) -> Principal:
    try:
        claims = _decode_unverified_payload(token)
        if settings.jwt_public_key:
            jwt.decode(
                token,
                key=settings.jwt_public_key,
                audience=settings.audience,
                issuer=settings.issuer,
                algorithms=[settings.algorithm],
            )
    except JWTError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from error

    raw_roles = claims.get("roles", []) or claims.get("role", [])
    if isinstance(raw_roles, str):
        raw_roles = [raw_roles]
    roles = [Role(role_value) for role_value in raw_roles]
    permissions = sorted(permissions_for_roles(roles), key=lambda item: item.value)
    return Principal(
        subject=str(claims.get("sub", "")),
        roles=roles,
        permissions=permissions,
        agency_id=claims.get("agency_id"),
    )


def principal_from_request(request: Request, settings: AuthSettings | None = None) -> Principal:
    auth_settings = settings or AuthSettings()
    authorization_header = request.headers.get("authorization")
    if not authorization_header:
        if auth_settings.mode == "development":
            return _principal_from_dev_headers(request, auth_settings)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    scheme, _, token = authorization_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")

    if auth_settings.mode == "development" and token.lower() == "development-token":
        return _principal_from_dev_headers(request, auth_settings)

    return _principal_from_jwt(token, auth_settings)


def has_permission(principal: Principal, permission: Permission) -> bool:
    return permission in principal.permissions


def has_any_role(principal: Principal, roles: Iterable[Role]) -> bool:
    principal_roles = set(principal.roles)
    return any(role in principal_roles for role in roles)