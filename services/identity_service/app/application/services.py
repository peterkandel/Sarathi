from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status

from app.application.security import TokenService
from app.domain.events import AuditEvent
from app.domain.models import AuditEvent as AuditEventModel
from app.domain.models import PasswordResetToken, Role, Session, User
from app.infrastructure.repositories import AuditRepository, PasswordResetRepository, SessionRepository, UserRepository


class IdentityService:
    def __init__(
        self,
        user_repository: UserRepository,
        session_repository: SessionRepository,
        password_reset_repository: PasswordResetRepository,
        audit_repository: AuditRepository,
        token_service: TokenService | None = None,
    ) -> None:
        self.users = user_repository
        self.sessions = session_repository
        self.password_resets = password_reset_repository
        self.audit = audit_repository
        self.tokens = token_service or TokenService()

    async def register(self, *, email: str, username: str, password: str, full_name: str | None = None, actor_id: UUID | None = None) -> User:
        existing_user = await self.users.get_by_email_or_username(email)
        if existing_user is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        existing_user = await self.users.get_by_email_or_username(username)
        if existing_user is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")

        user = User(
            email=email.lower(),
            username=username,
            password_hash=self.tokens.hash_password(password),
            full_name=full_name,
            is_active=True,
            is_locked=False,
            password_changed_at=datetime.now(timezone.utc),
            created_by_actor_id=actor_id,
            updated_by_actor_id=actor_id,
        )
        citizen_role = await self.users.get_role_by_name("Citizen")
        if citizen_role is None:
            citizen_role = await self.users.create_role(Role(name="Citizen", description="Default citizen role", is_system=True))
        user.roles = [citizen_role]
        created_user = await self.users.create_user(user)
        await self.audit.record_event(
            AuditEventModel(
                event_type="UserRegistered",
                aggregate_id=created_user.id,
                payload={"email": created_user.email, "username": created_user.username},
            )
        )
        return created_user

    async def login(self, *, identifier: str, password: str, device_id: str | None = None, ip_address: str | None = None, user_agent: str | None = None) -> tuple[str, str, int, Session, User]:
        user = await self.users.get_by_email_or_username(identifier.lower())
        if user is None or not self.tokens.verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.is_active or user.is_locked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

        access_token, access_jti, expires_in = self.tokens.create_access_token(user)
        refresh_token, refresh_jti, refresh_hash, refresh_expires_at = self.tokens.create_refresh_token()
        session = Session(
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            access_token_jti=access_jti,
            refresh_token_jti=refresh_jti,
            expires_at=refresh_expires_at,
            device_id=device_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_metadata={"login_at": datetime.now(timezone.utc).isoformat()},
        )
        created_session = await self.sessions.create_session(session)
        await self.audit.record_event(
            AuditEventModel(
                event_type="UserLoggedIn",
                aggregate_id=user.id,
                payload={"session_id": str(created_session.id), "device_id": device_id},
            )
        )
        user.last_login_at = datetime.now(timezone.utc)
        await self.users.update_user(user)
        return access_token, refresh_token, expires_in, created_session, user

    async def refresh(self, *, session_id: UUID, refresh_token: str) -> tuple[str, str, int, Session, User]:
        session = await self.sessions.get_active_session(session_id)
        if session is None or session.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is not active")
        if session.refresh_token_hash != self.tokens.hash_token(refresh_token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user = await self.users.get_by_id(session.user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        access_token, access_jti, expires_in = self.tokens.create_access_token(user)
        new_refresh_token, new_refresh_jti, new_refresh_hash, new_refresh_expires_at = self.tokens.create_refresh_token()
        session.refresh_token_hash = new_refresh_hash
        session.refresh_token_jti = new_refresh_jti
        session.access_token_jti = access_jti
        session.expires_at = new_refresh_expires_at
        session.last_used_at = datetime.now(timezone.utc)
        await self.sessions.update_session(session)
        await self.audit.record_event(
            AuditEventModel(
                event_type="TokenRefreshed",
                aggregate_id=user.id,
                payload={"session_id": str(session.id)},
            )
        )
        return access_token, new_refresh_token, expires_in, session, user

    async def logout(self, *, session_id: UUID, actor_id: UUID | None = None) -> None:
        session = await self.sessions.revoke_session(session_id, datetime.now(timezone.utc))
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        await self.audit.record_event(
            AuditEventModel(
                event_type="UserLoggedOut",
                aggregate_id=session.user_id,
                payload={"session_id": str(session_id), "actor_id": str(actor_id) if actor_id else None},
            )
        )

    async def request_password_reset(self, *, email: str, requested_by_ip: str | None = None) -> str:
        user = await self.users.get_by_email_or_username(email.lower())
        if user is None:
            return "If the account exists, a reset link has been sent."
        token, token_hash, expires_at = self.tokens.create_password_reset_token()
        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            requested_by_ip=requested_by_ip,
        )
        await self.password_resets.create_reset_token(reset_record)
        await self.audit.record_event(
            AuditEventModel(
                event_type="PasswordResetRequested",
                aggregate_id=user.id,
                payload={"requested_by_ip": requested_by_ip},
            )
        )
        return token

    async def confirm_password_reset(self, *, token: str, new_password: str) -> None:
        token_hash = self.tokens.hash_token(token)
        reset_record = await self.password_resets.get_active_token(token_hash)
        if reset_record is None or reset_record.used_at is not None or reset_record.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
        user = await self.users.get_by_id(reset_record.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.password_hash = self.tokens.hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        await self.users.update_user(user)
        await self.password_resets.mark_used(reset_record.id, datetime.now(timezone.utc))
        await self.audit.record_event(
            AuditEventModel(
                event_type="PasswordResetCompleted",
                aggregate_id=user.id,
                payload={"reset_token_id": str(reset_record.id)},
            )
        )

    async def list_users(self) -> list[User]:
        return await self.users.list_users()
