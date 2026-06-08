"""User account endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.openapi import (
    USER_ALARM_EXAMPLE,
    USER_DETAIL_EXAMPLE,
    USER_FCM_TOKEN_EXAMPLE,
    error_responses,
    success_response,
)
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import (
    ApiResponse,
    UserAlarmRequest,
    UserDetailResponse,
    UserFcmTokenRequest,
)
from app.services.user_auth_service import UserAuthService


router = APIRouter(prefix="/v1/user", tags=["사용자"])


@router.get(
    "/detail",
    response_model=ApiResponse[UserDetailResponse],
    response_model_exclude_none=True,
    summary="내 정보 조회",
    description="현재 로그인한 사용자의 상세 정보를 조회합니다.",
    responses={
        200: success_response(USER_DETAIL_EXAMPLE),
        **error_responses(AppError.INVALID_TOKEN, AppError.USER_NOT_FOUND),
    },
)
def get_user_detail(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserAuthService(db=db)
    data = service.get_user_detail(current_user)
    return {"success": True, "data": data.model_dump(by_alias=True)}


@router.patch(
    "/alarm",
    summary="알림 설정 변경",
    description="현재 사용자의 알림 수신 여부를 변경합니다.",
    responses={
        200: success_response(USER_ALARM_EXAMPLE),
        **error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR, AppError.USER_NOT_FOUND),
    },
)
@router.post(
    "/alarm",
    summary="알림 설정 변경",
    description="현재 사용자의 알림 수신 여부를 변경합니다.",
    responses={
        200: success_response(USER_ALARM_EXAMPLE),
        **error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR, AppError.USER_NOT_FOUND),
    },
)
def update_alarm(
    payload: UserAlarmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserAuthService(db=db)
    service.update_alarm(current_user, payload.alarm_enabled)
    return {"success": True, "data": None, "message": "알람 설정이 업데이트되었습니다."}


@router.patch(
    "/fcm-token",
    summary="FCM 토큰 저장",
    description="현재 사용자의 FCM 토큰을 저장하거나 갱신합니다.",
    responses={
        200: success_response(USER_FCM_TOKEN_EXAMPLE),
        **error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR, AppError.USER_NOT_FOUND),
    },
)
def update_fcm_token(
    payload: UserFcmTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserAuthService(db=db)
    service.upsert_fcm_token(current_user, payload.fcm_token)
    return {"success": True, "data": None, "message": "FCM 토큰이 업데이트되었습니다."}
