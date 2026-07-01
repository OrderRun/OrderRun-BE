"""Phone-auth endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.openapi import AUTH_ERROR_RESPONSES, error_responses, success_response
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
from app.services.user_auth.phone_verification_service import PhoneVerificationService
from app.services.user_auth.user_auth_service import UserAuthService


router = APIRouter(prefix="/auth", tags=["인증"])


VERIFICATION_SEND_EXAMPLE = {
    "success": True,
    "data": {"phone": "01012345678", "expiresAt": "2026-06-01T12:05:00+09:00"},
    "message": None,
}
TOKEN_EXAMPLE = {
    "success": True,
    "data": {
        "accessToken": "access-token",
        "refreshToken": "refresh-token",
        "tokenType": "Bearer",
        "expiresIn": 3600000,
        "userId": "550e8400-e29b-41d4-a716-446655440000",
    },
    "message": None,
}


@router.post(
    "/signup/send",
    response_model=ApiResponse[AuthVerificationSendResponse],
    summary="회원가입 인증번호 발송",
    description="이름, 전화번호, 통신사를 받아 회원가입용 SMS 인증번호를 발송합니다.",
    responses={
        200: success_response(VERIFICATION_SEND_EXAMPLE),
        **error_responses(
            AppError.VALIDATION_ERROR,
            AppError.SMS_SENDER_NOT_CONFIGURED,
            AppError.PHONE_ALREADY_EXISTS,
            AppError.PHONE_VERIFICATION_ALREADY_SENT,
        ),
    },
)
def signup_send(
    payload: AuthSignupSendRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    sms_sender=Depends(get_sms_sender),
):
    verification_service = PhoneVerificationService(sms_sender)
    data = UserAuthService.send_signup_verification(db, verification_service, payload, background_tasks)
    return {"success": True, "data": data.model_dump(by_alias=True)}


@router.post(
    "/signup/confirm",
    response_model=ApiResponse[AuthTokenResponse],
    summary="회원가입 인증번호 확인",
    description="회원가입 인증번호를 확인하고 신규 사용자를 생성한 뒤 토큰을 발급합니다.",
    responses={
        200: success_response(TOKEN_EXAMPLE),
        **error_responses(
            AppError.VALIDATION_ERROR,
            AppError.PHONE_ALREADY_EXISTS,
            AppError.PHONE_VERIFICATION_NOT_FOUND,
            AppError.PHONE_VERIFICATION_EXPIRED,
            AppError.PHONE_VERIFICATION_CODE_MISMATCH,
        ),
    },
)
def signup_confirm(
    payload: AuthPhoneConfirmRequest,
    db: Session = Depends(get_db),
    sms_sender=Depends(get_sms_sender),
):
    verification_service = PhoneVerificationService(sms_sender)
    data = UserAuthService.confirm_signup(db, verification_service, payload)
    return {"success": True, "data": data.model_dump(by_alias=True)}


@router.post(
    "/login/send",
    response_model=ApiResponse[AuthVerificationSendResponse],
    summary="로그인 인증번호 발송",
    description="가입된 전화번호로 로그인용 SMS 인증번호를 발송합니다.",
    responses={
        200: success_response(VERIFICATION_SEND_EXAMPLE),
        **error_responses(
            AppError.VALIDATION_ERROR,
            AppError.SMS_SENDER_NOT_CONFIGURED,
            AppError.INVALID_CREDENTIALS,
            AppError.PHONE_VERIFICATION_ALREADY_SENT,
        ),
    },
)
def login_send(
    payload: AuthLoginSendRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    sms_sender=Depends(get_sms_sender),
):
    verification_service = PhoneVerificationService(sms_sender)
    data = UserAuthService.send_login_verification(db, verification_service, payload, background_tasks)
    return {"success": True, "data": data.model_dump(by_alias=True)}


@router.post(
    "/login/confirm",
    response_model=ApiResponse[AuthTokenResponse],
    summary="로그인 인증번호 확인",
    description="로그인 인증번호를 확인하고 액세스 토큰과 리프레시 토큰을 발급합니다.",
    responses={
        200: success_response(TOKEN_EXAMPLE),
        **error_responses(
            AppError.VALIDATION_ERROR,
            AppError.USER_NOT_FOUND,
            AppError.PHONE_VERIFICATION_NOT_FOUND,
            AppError.PHONE_VERIFICATION_EXPIRED,
            AppError.PHONE_VERIFICATION_CODE_MISMATCH,
        ),
    },
)
def login_confirm(
    payload: AuthLoginConfirmRequest,
    db: Session = Depends(get_db),
    sms_sender=Depends(get_sms_sender),
):
    verification_service = PhoneVerificationService(sms_sender)
    data = UserAuthService.confirm_login(db, verification_service, payload)
    return {"success": True, "data": data.model_dump(by_alias=True)}


@router.post(
    "/refresh",
    response_model=ApiResponse[AuthAccessTokenResponse],
    summary="액세스 토큰 재발급",
    description="리프레시 토큰을 검증해 새 액세스 토큰을 발급합니다.",
    responses={
        200: success_response(
            {
                "success": True,
                "data": {"accessToken": "access-token", "expiresIn": 3600000},
                "message": None,
            }
        ),
        **error_responses(AppError.VALIDATION_ERROR, AppError.INVALID_TOKEN, AppError.USER_NOT_FOUND),
    },
)
def refresh_token(
    payload: AuthRefreshRequest,
    db: Session = Depends(get_db),
):
    data = UserAuthService.refresh_access_token(db, payload)
    return {"success": True, "data": data.model_dump(by_alias=True)}


@router.post(
    "/logout",
    summary="로그아웃",
    description="현재 사용자의 로그아웃 요청을 처리합니다.",
    responses={
        200: success_response({"success": True, "data": None, "message": "로그아웃 되었습니다."}),
        **AUTH_ERROR_RESPONSES,
        **error_responses(AppError.VALIDATION_ERROR),
    },
)
def logout(
    payload: AuthLogoutRequest,
    current_user: User = Depends(get_current_user),
):
    _ = payload
    _ = current_user
    return {"success": True, "data": None, "message": "로그아웃 되었습니다."}
