from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ..application.exceptions import AuthenticationError
from ..domain.security import Principal, TokenClaims
from ..infrastructure.config import AuthSettings

bearer_scheme = HTTPBearer(auto_error=False)


def decode_access_token(token: str, settings: AuthSettings) -> TokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            audience=settings.audience,
            issuer=settings.issuer,
            options={"verify_aud": bool(settings.audience), "verify_iss": bool(settings.issuer)},
            leeway=settings.leeway_seconds,
        )
    except JWTError as exc:
        raise AuthenticationError("Invalid access token") from exc

    claims = TokenClaims.model_validate(payload)
    if claims.sub != payload.get("sub"):
        raise AuthenticationError("Token subject is missing")
    return claims


def build_principal(claims: TokenClaims) -> Principal:
    return Principal(
        subject=claims.sub,
        email=claims.email,
        roles=list(dict.fromkeys(claims.roles)),
        permissions=list(dict.fromkeys(claims.permissions)),
        tenant_id=claims.tenant_id,
        agency_id=claims.agency_id,
    )


def get_current_principal_dependency(settings: AuthSettings) -> Callable[[HTTPAuthorizationCredentials | None], Principal]:
    async def dependency(credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme)) -> Principal:
        if credentials is None or not credentials.credentials:
            raise AuthenticationError("Missing bearer token")

        claims = decode_access_token(credentials.credentials, settings)
        return build_principal(claims)

    return dependency


def claims_to_dict(claims: TokenClaims) -> dict[str, Any]:
    return claims.model_dump(exclude_none=True)
