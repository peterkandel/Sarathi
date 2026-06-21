from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import AuditEvent, PasswordResetToken, Permission, Role, Session, User, role_permissions, user_roles


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_user(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def update_user(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.id == user_id, User.deleted_at.is_(None))
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_email_or_username(self, identifier: str) -> User | None:
        statement = select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(
            User.deleted_at.is_(None),
            (User.email == identifier) | (User.username == identifier),
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_users(self) -> list[User]:
        statement = select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.deleted_at.is_(None)).order_by(User.created_at.desc())
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all())

    async def create_role(self, role: Role) -> Role:
        self.session.add(role)
        await self.session.flush()
        return role

    async def get_role_by_name(self, name: str) -> Role | None:
        statement = select(Role).where(Role.name == name, Role.deleted_at.is_(None))
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_roles(self, user_id: UUID) -> Sequence[Role]:
        statement = select(Role).join(user_roles, Role.id == user_roles.c.role_id).where(user_roles.c.user_id == user_id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_permissions(self, role_ids: Sequence[UUID]) -> Sequence[Permission]:
        if not role_ids:
            return []
        statement = select(Permission).join(role_permissions, Permission.id == role_permissions.c.permission_id).where(role_permissions.c.role_id.in_(role_ids))
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class SessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_session(self, session: Session) -> Session:
        self.session.add(session)
        await self.session.flush()
        return session

    async def get_active_session(self, session_id: UUID) -> Session | None:
        statement = select(Session).where(Session.id == session_id, Session.revoked_at.is_(None), Session.deleted_at.is_(None))
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def revoke_session(self, session_id: UUID, revoked_at: datetime) -> Session | None:
        session = await self.get_active_session(session_id)
        if session is None:
            return None
        session.revoked_at = revoked_at
        await self.session.flush()
        return session

    async def update_session(self, session: Session) -> Session:
        self.session.add(session)
        await self.session.flush()
        return session


class PasswordResetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_reset_token(self, token: PasswordResetToken) -> PasswordResetToken:
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_active_token(self, token_hash: str) -> PasswordResetToken | None:
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.deleted_at.is_(None),
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def mark_used(self, token_id: UUID, used_at: datetime) -> PasswordResetToken | None:
        statement = select(PasswordResetToken).where(PasswordResetToken.id == token_id)
        result = await self.session.execute(statement)
        token = result.scalar_one_or_none()
        if token is None:
            return None
        token.used_at = used_at
        await self.session.flush()
        return token


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(self, event: AuditEvent) -> AuditEvent:
        self.session.add(event)
        await self.session.flush()
        return event
