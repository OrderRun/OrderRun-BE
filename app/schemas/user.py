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
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=1, max_length=20)
    carrier: str = Field(..., min_length=1, max_length=50)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("name", "phone", "carrier")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class AuthPhoneConfirmRequest(BaseModel):
    phone: str = Field(..., min_length=1, max_length=20)
    code: str = Field(..., min_length=1, max_length=20)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("phone", "code")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class AuthLoginSendRequest(BaseModel):
    phone: str = Field(..., min_length=1, max_length=20)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("phone")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class AuthLoginConfirmRequest(AuthPhoneConfirmRequest):
    fcm_token: Optional[str] = Field(None, alias="fcmToken", min_length=1, max_length=4096)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

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
    refresh_token: str = Field(..., alias="refreshToken", min_length=1)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("refresh_token")
    @classmethod
    def strip_refresh_token(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("refreshToken must not be blank")
        return stripped


class AuthLogoutRequest(BaseModel):
    refresh_token: str = Field(..., alias="refreshToken", min_length=1)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("refresh_token")
    @classmethod
    def strip_refresh_token(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("refreshToken must not be blank")
        return stripped


class AuthVerificationSendResponse(BaseModel):
    phone: str
    expires_at: datetime = Field(..., alias="expiresAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class AuthTokenResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")
    token_type: str = Field("Bearer", alias="tokenType")
    expires_in: int = Field(..., alias="expiresIn")
    user_id: str = Field(..., alias="userId")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class AuthAccessTokenResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    expires_in: int = Field(..., alias="expiresIn")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class UserDetailResponse(BaseModel):
    id: str
    name: str
    phone: Optional[str] = None
    phone_verified_at: Optional[datetime] = Field(None, alias="phoneVerifiedAt")
    created_at: datetime = Field(..., alias="createdAt")
    last_login_at: Optional[datetime] = Field(None, alias="lastLoginAt")
    alarm_enabled: bool = Field(..., alias="alarmEnabled")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class UserAlarmRequest(BaseModel):
    alarm_enabled: bool = Field(..., alias="alarmEnabled")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class UserFcmTokenRequest(BaseModel):
    fcm_token: str = Field(..., alias="fcmToken", min_length=1, max_length=4096)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("fcm_token")
    @classmethod
    def strip_fcm_token(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("fcmToken must not be blank")
        return stripped
