"""Notification request and response schemas."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models.notification import (
    DevicePlatform,
    NotificationType,
    NotificationStatus
)


# ========== Device Token Schemas ==========

class DeviceTokenCreate(BaseModel):
    """Schema for creating a new device token."""
    token: str = Field(..., min_length=1, max_length=255, description="FCM 디바이스 토큰")
    platform: DevicePlatform = Field(..., description="디바이스 플랫폼(ios, android, web)")
    device_id: Optional[str] = Field(None, max_length=255, description="디바이스 식별자")

    model_config = ConfigDict(from_attributes=True)


class DeviceTokenResponse(BaseModel):
    """Schema for device token response."""
    id: int
    user_id: str
    token: str
    platform: DevicePlatform
    device_id: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class DeviceTokenUpdate(BaseModel):
    """Schema for updating a device token."""
    is_active: Optional[bool] = Field(None, description="토큰 활성 여부")

    model_config = ConfigDict(from_attributes=True)


# ========== Notification Schemas ==========

class NotificationCreate(BaseModel):
    """Schema for creating a notification (internal use)."""
    user_id: str = Field(..., description="알림을 받을 사용자 ID")
    notification_type: NotificationType = Field(..., description="알림 유형")
    title: str = Field(..., min_length=1, max_length=255, description="알림 제목")
    body: str = Field(..., min_length=1, description="알림 본문")
    data: Optional[Dict[str, Any]] = Field(None, description="추가 payload 데이터")
    related_entity_type: Optional[str] = Field(None, max_length=50, description="관련 엔티티 유형")
    related_entity_id: Optional[int] = Field(None, description="관련 엔티티 ID")

    model_config = ConfigDict(from_attributes=True)


class NotificationSendRequest(BaseModel):
    """Schema for sending a notification via API."""
    notification_type: NotificationType = Field(..., description="알림 유형")
    title: str = Field(..., min_length=1, max_length=255, description="알림 제목")
    body: str = Field(..., min_length=1, description="알림 본문")
    data: Optional[Dict[str, Any]] = Field(None, description="추가 payload 데이터")
    related_entity_type: Optional[str] = Field(None, max_length=50, description="관련 엔티티 유형")
    related_entity_id: Optional[int] = Field(None, description="관련 엔티티 ID")

    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    id: int
    user_id: str
    notification_type: NotificationType
    title: str
    body: str
    data: Optional[str]  # JSON string
    related_entity_type: Optional[str]
    related_entity_id: Optional[int]
    status: NotificationStatus
    fcm_message_id: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """Schema for list of notifications with pagination."""
    total: int
    notifications: list[NotificationResponse]
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


class NotificationMarkReadRequest(BaseModel):
    """Schema for marking notification(s) as read."""
    notification_ids: list[int] = Field(..., min_length=1, description="읽음 처리할 알림 ID 목록")

    model_config = ConfigDict(from_attributes=True)


# ========== Notification Preference Schemas ==========

class NotificationPreferenceResponse(BaseModel):
    """Schema for notification preference response."""
    id: int
    user_id: str
    enable_proposal_notifications: bool
    enable_offer_notifications: bool
    enable_mission_notifications: bool
    enable_payment_notifications: bool
    enable_system_notifications: bool
    enable_quiet_hours: bool
    quiet_hours_start: Optional[int]
    quiet_hours_end: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences."""
    enable_proposal_notifications: Optional[bool] = None
    enable_offer_notifications: Optional[bool] = None
    enable_mission_notifications: Optional[bool] = None
    enable_payment_notifications: Optional[bool] = None
    enable_system_notifications: Optional[bool] = None
    enable_quiet_hours: Optional[bool] = None
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23, description="방해 금지 시작 시각(0-23)")
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23, description="방해 금지 종료 시각(0-23)")

    model_config = ConfigDict(from_attributes=True)


# ========== FCM Specific Schemas ==========

class FCMNotificationPayload(BaseModel):
    """Schema for FCM notification payload."""
    title: str = Field(..., description="알림 제목")
    body: str = Field(..., description="알림 본문")
    image: Optional[str] = Field(None, description="알림 이미지 URL")

    model_config = ConfigDict(from_attributes=True)


class FCMDataPayload(BaseModel):
    """Schema for FCM data payload."""
    notification_id: str = Field(..., description="내부 알림 ID")
    notification_type: str = Field(..., description="알림 유형")
    related_entity_type: Optional[str] = Field(None, description="관련 엔티티 유형")
    related_entity_id: Optional[str] = Field(None, description="관련 엔티티 ID")
    custom_data: Optional[Dict[str, str]] = Field(None, description="추가 데이터")

    model_config = ConfigDict(from_attributes=True)


class FCMSendResult(BaseModel):
    """Schema for FCM send result."""
    success: bool = Field(..., description="발송 성공 여부")
    message_id: Optional[str] = Field(None, description="FCM 메시지 ID")
    error_code: Optional[str] = Field(None, description="실패 시 에러 코드")
    error_message: Optional[str] = Field(None, description="실패 시 에러 메시지")

    model_config = ConfigDict(from_attributes=True)
