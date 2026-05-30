"""User account endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import (
    ApiResponse,
    UserAlarmRequest,
    UserDetailResponse,
    UserFcmTokenRequest,
)
from app.services.user_auth_service import UserAuthService


router = APIRouter(prefix="/v1/user", tags=["user"])


@router.get("/detail", response_model=ApiResponse[UserDetailResponse], response_model_exclude_none=True)
def get_user_detail(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserAuthService(db=db)
    data = service.get_user_detail(current_user)
    return {"success": True, "data": data.model_dump(by_alias=True)}


@router.post("/alarm")
def update_alarm(
    payload: UserAlarmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserAuthService(db=db)
    service.update_alarm(current_user, payload.alarm_enabled)
    return {"success": True, "data": None, "message": "알람 설정이 업데이트되었습니다."}


@router.patch("/fcm-token")
def update_fcm_token(
    payload: UserFcmTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserAuthService(db=db)
    service.upsert_fcm_token(current_user, payload.fcm_token)
    return {"success": True, "data": None, "message": "FCM 토큰이 업데이트되었습니다."}
