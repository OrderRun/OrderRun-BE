"""Schemas for user and phone-auth endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    timestamp: datetime


class AuthSignupSendRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="사용자 이름")
    phone: str = Field(..., min_length=1, max_length=20, description="휴대폰 번호")
    carrier: str = Field(..., min_length=1, max_length=50, description="통신사")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={"example": {"name": "홍길동", "phone": "01012345678", "carrier": "SKT"}},
    )

    @field_validator("name", "phone", "carrier")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class AuthPhoneConfirmRequest(BaseModel):
    phone: str = Field(..., min_length=1, max_length=20, description="휴대폰 번호")
    code: str = Field(..., min_length=1, max_length=20, description="SMS 인증번호")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={"example": {"phone": "01012345678", "code": "123456"}},
    )

    @field_validator("phone", "code")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class AuthLoginSendRequest(BaseModel):
    phone: str = Field(..., min_length=1, max_length=20, description="휴대폰 번호")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={"example": {"phone": "01012345678"}},
    )

    @field_validator("phone")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class AuthLoginConfirmRequest(BaseModel):
    phone: str = Field(..., min_length=1, max_length=20, description="휴대폰 번호")
    code: str = Field(..., min_length=1, max_length=20, description="SMS 인증번호")
    fcm_token: Optional[str] = Field(None, alias="fcmToken", min_length=1, max_length=4096, description="FCM 토큰")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={"example": {"phone": "01012345678", "code": "123456", "fcmToken": "fcm-token"}},
    )

    @field_validator("phone", "code")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("fcm_token")
    @classmethod
    def strip_fcm_token(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("fcmToken must not be blank")
        return stripped


class AuthRefreshRequest(BaseModel):
    refresh_token: str = Field(..., alias="refreshToken", min_length=1, description="리프레시 토큰")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={"example": {"refreshToken": "refresh-token"}},
    )

    @field_validator("refresh_token")
    @classmethod
    def strip_refresh_token(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("refreshToken must not be blank")
        return stripped


class AuthLogoutRequest(BaseModel):
    refresh_token: str = Field(..., alias="refreshToken", min_length=1, description="리프레시 토큰")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={"example": {"refreshToken": "refresh-token"}},
    )

    @field_validator("refresh_token")
    @classmethod
    def strip_refresh_token(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("refreshToken must not be blank")
        return stripped


class AuthVerificationSendResponse(BaseModel):
    phone: str = Field(..., description="인증번호를 발송한 휴대폰 번호")
    expires_at: datetime = Field(..., alias="expiresAt", description="인증번호 만료 시각")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_schema_extra={"example": {"phone": "01012345678", "expiresAt": "2026-06-01T12:05:00+09:00"}},
    )


class AuthTokenResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken", description="액세스 토큰")
    refresh_token: str = Field(..., alias="refreshToken", description="리프레시 토큰")
    token_type: str = Field("Bearer", alias="tokenType", description="토큰 타입")
    expires_in: int = Field(..., alias="expiresIn", description="액세스 토큰 만료 시간(밀리초)")
    user_id: str = Field(..., alias="userId", description="사용자 ID")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_schema_extra={
            "example": {
                "accessToken": "access-token",
                "refreshToken": "refresh-token",
                "tokenType": "Bearer",
                "expiresIn": 3600000,
                "userId": "550e8400-e29b-41d4-a716-446655440000",
            }
        },
    )


class AuthAccessTokenResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken", description="액세스 토큰")
    expires_in: int = Field(..., alias="expiresIn", description="액세스 토큰 만료 시간(밀리초)")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_schema_extra={"example": {"accessToken": "access-token", "expiresIn": 3600000}},
    )


class UserDetailResponse(BaseModel):
    id: str = Field(..., description="사용자 ID")
    name: str = Field(..., description="사용자 이름")
    phone: Optional[str] = Field(None, description="휴대폰 번호")
    phone_verified_at: Optional[datetime] = Field(None, alias="phoneVerifiedAt", description="휴대폰 인증 시각")
    created_at: datetime = Field(..., alias="createdAt", description="가입 시각")
    last_login_at: Optional[datetime] = Field(None, alias="lastLoginAt", description="마지막 로그인 시각")
    alarm_enabled: bool = Field(..., alias="alarmEnabled", description="알림 수신 여부")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class UserAlarmRequest(BaseModel):
    alarm_enabled: bool = Field(..., alias="alarmEnabled", description="알림 수신 여부")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class UserFcmTokenRequest(BaseModel):
    fcm_token: str = Field(..., alias="fcmToken", min_length=1, max_length=4096, description="FCM 토큰")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("fcm_token")
    @classmethod
    def strip_fcm_token(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("fcmToken must not be blank")
        return stripped
