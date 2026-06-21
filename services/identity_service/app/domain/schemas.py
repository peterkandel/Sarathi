from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RoleRead(BaseModel):
    id: UUID
    name: str
    description: str | None = None


class PermissionRead(BaseModel):
    id: UUID
    code: str
    description: str | None = None


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    full_name: str | None = None
    is_active: bool
    roles: list[RoleRead] = Field(default_factory=list)


class SessionRead(BaseModel):
    id: UUID
    user_id: UUID
    expires_at: datetime
    revoked_at: datetime | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 10:
            raise ValueError("password must be at least 10 characters")
        return value


class LoginRequest(BaseModel):
    identifier: str
    password: str
    device_id: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str
    session_id: UUID


class LogoutRequest(BaseModel):
    session_id: UUID


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 10:
            raise ValueError("password must be at least 10 characters")
        return value


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    session_id: UUID
    user: UserRead


class MessageResponse(BaseModel):
    message: str


class AuthorizationCheckRequest(BaseModel):
    role: str | None = None
    permission: str | None = None
