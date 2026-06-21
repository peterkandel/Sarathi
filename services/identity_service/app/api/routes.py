from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.application.services import IdentityService
from app.application.security import TokenService
from app.api.dependencies import get_audit_repository, get_password_reset_repository, get_session_repository, get_user_repository
from app.domain.schemas import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
    TokenPairResponse,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_identity_service(
    user_repository=Depends(get_user_repository),
    session_repository=Depends(get_session_repository),
    password_reset_repository=Depends(get_password_reset_repository),
    audit_repository=Depends(get_audit_repository),
) -> IdentityService:
    return IdentityService(
        user_repository=user_repository,
        session_repository=session_repository,
        password_reset_repository=password_reset_repository,
        audit_repository=audit_repository,
        token_service=TokenService(),
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, service: IdentityService = Depends(get_identity_service)) -> UserRead:
    user = await service.register(email=payload.email, username=payload.username, password=payload.password, full_name=payload.full_name)
    return UserRead.model_validate(user, from_attributes=True)


@router.post("/login", response_model=TokenPairResponse)
async def login(payload: LoginRequest, request: Request, service: IdentityService = Depends(get_identity_service)) -> TokenPairResponse:
    access_token, refresh_token, expires_in, session, user = await service.login(
        identifier=payload.identifier,
        password=payload.password,
        device_id=payload.device_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        session_id=session.id,
        user=UserRead.model_validate(user, from_attributes=True),
    )


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(payload: dict[str, str], service: IdentityService = Depends(get_identity_service)) -> TokenPairResponse:
    try:
        session_id = UUID(payload["session_id"])
        refresh_token = payload["refresh_token"]
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="session_id and refresh_token are required") from exc

    access_token, new_refresh_token, expires_in, session, user = await service.refresh(session_id=session_id, refresh_token=refresh_token)
    return TokenPairResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=expires_in,
        session_id=session.id,
        user=UserRead.model_validate(user, from_attributes=True),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(payload: LogoutRequest, service: IdentityService = Depends(get_identity_service)) -> MessageResponse:
    await service.logout(session_id=payload.session_id)
    return MessageResponse(message="Logged out")


@router.post("/password-reset/request", response_model=MessageResponse)
async def password_reset_request(payload: PasswordResetRequest, request: Request, service: IdentityService = Depends(get_identity_service)) -> MessageResponse:
    await service.request_password_reset(email=payload.email, requested_by_ip=request.client.host if request.client else None)
    return MessageResponse(message="If the account exists, a reset link has been sent.")


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def password_reset_confirm(payload: PasswordResetConfirmRequest, service: IdentityService = Depends(get_identity_service)) -> MessageResponse:
    await service.confirm_password_reset(token=payload.token, new_password=payload.new_password)
    return MessageResponse(message="Password updated")


@router.get("/admin/users", response_model=list[UserRead])
async def list_users(service: IdentityService = Depends(get_identity_service)) -> list[UserRead]:
    users = await service.list_users()
    return [UserRead.model_validate(user, from_attributes=True) for user in users]
