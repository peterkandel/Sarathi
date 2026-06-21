from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import get_session
from app.infrastructure.repositories import AuditRepository, PasswordResetRepository, SessionRepository, UserRepository


async def get_user_repository(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


async def get_session_repository(session: AsyncSession = Depends(get_session)) -> SessionRepository:
    return SessionRepository(session)


async def get_password_reset_repository(session: AsyncSession = Depends(get_session)) -> PasswordResetRepository:
    return PasswordResetRepository(session)


async def get_audit_repository(session: AsyncSession = Depends(get_session)) -> AuditRepository:
    return AuditRepository(session)
