from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID, uuid4

from jose import JWTError, jwt
from passlib.hash import pbkdf2_sha256

from app.core.config import settings
from app.domain.models import Permission, Role, Session, User


class TokenService:
    def __init__(self) -> None:
        self._secret_key = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._issuer = settings.jwt_issuer
        self._audience = settings.jwt_audience
        self._access_ttl_minutes = settings.access_token_ttl_minutes
        self._refresh_ttl_days = settings.refresh_token_ttl_days

    def hash_password(self, password: str) -> str:
        return pbkdf2_sha256.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        return pbkdf2_sha256.verify(password, password_hash)

    def create_access_token(self, user: User) -> tuple[str, str, int]:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self._access_ttl_minutes)
        jti = str(uuid4())
        payload = {
            "sub": str(user.id),
            "iss": self._issuer,
            "aud": self._audience,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "jti": jti,
            "roles": [role.name for role in user.roles],
            "permissions": self._collect_permissions(user),
            "email": user.email,
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm), jti, self._access_ttl_minutes * 60

    def create_refresh_token(self) -> tuple[str, str, str, datetime]:
        token = token_urlsafe(48)
        refresh_jti = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=self._refresh_ttl_days)
        return token, refresh_jti, self.hash_token(token), expires_at

    def create_password_reset_token(self) -> tuple[str, str, datetime]:
        token = token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_ttl_minutes)
        return token, self.hash_token(token), expires_at

    def hash_token(self, token: str) -> str:
        return sha256(token.encode("utf-8")).hexdigest()

    def verify_access_token(self, token: str) -> dict[str, object]:
        return jwt.decode(
            token,
            self._secret_key,
            algorithms=[self._algorithm],
            audience=self._audience,
            issuer=self._issuer,
            options={"verify_aud": bool(self._audience), "verify_iss": bool(self._issuer)},
        )

    @staticmethod
    def _collect_permissions(user: User) -> list[str]:
        permissions: set[str] = set()
        for role in user.roles:
            for permission in role.permissions:
                permissions.add(permission.code)
        return sorted(permissions)
