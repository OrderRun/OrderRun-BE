"""Phone-auth endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import (
    ApiResponse,
    AuthAccessTokenResponse,
    AuthLoginConfirmRequest,
    AuthLoginSendRequest,
    AuthLogoutRequest,
    AuthPhoneConfirmRequest,
    AuthRefreshRequest,
    AuthSignupSendRequest,
    AuthTokenResponse,
    AuthVerificationSendResponse,
)
from app.services.sms_service import get_sms_sender
from app.services.user_auth_service import UserAuthService


router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/signup/send", response_model=ApiResponse[AuthVerificationSendResponse], response_model_exclude_none=True)
def signup_send(
    payload: AuthSignupSendRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    sms_sender=Depends(get_sms_sender),
):
    service = UserAuthService(db=db, sms_sender=sms_sender)
    data = service.send_signup_verification(payload, background_tasks=background_tasks)
    return {"success": True, "data": data.model_dump(by_alias=True)}


@router.post("/signup/confirm", response_model=ApiResponse[AuthTokenResponse], response_model_exclude_none=True)
def signup_confirm(
    payload: AuthPhoneConfirmRequest,
    db: Session = Depends(get_db),
    sms_sender=Depends(get_sms_sender),
):
    service = UserAuthService(db=db, sms_sender=sms_sender)
    data = service.confirm_signup(payload)
    return {"success": True, "data": data.model_dump(by_alias=True)}


@router.post("/login/send", response_model=ApiResponse[AuthVerificationSendResponse], response_model_exclude_none=True)
def login_send(
    payload: AuthLoginSendRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    sms_sender=Depends(get_sms_sender),
):
    service = UserAuthService(db=db, sms_sender=sms_sender)
    data = service.send_login_verification(payload, background_tasks=background_tasks)
    return {"success": True, "data": data.model_dump(by_alias=True)}


@router.post("/login/confirm", response_model=ApiResponse[AuthTokenResponse], response_model_exclude_none=True)
def login_confirm(
    payload: AuthLoginConfirmRequest,
    db: Session = Depends(get_db),
    sms_sender=Depends(get_sms_sender),
):
    service = UserAuthService(db=db, sms_sender=sms_sender)
    data = service.confirm_login(payload)
    return {"success": True, "data": data.model_dump(by_alias=True)}


@router.post("/refresh", response_model=ApiResponse[AuthAccessTokenResponse], response_model_exclude_none=True)
def refresh_token(
    payload: AuthRefreshRequest,
    db: Session = Depends(get_db),
):
    service = UserAuthService(db=db)
    data = service.refresh_access_token(payload)
    return {"success": True, "data": data.model_dump(by_alias=True)}


@router.post("/logout")
def logout(
    payload: AuthLogoutRequest,
    current_user: User = Depends(get_current_user),
):
    _ = payload
    _ = current_user
    return {"success": True, "data": None, "message": "로그아웃 되었습니다."}
