"""Notification request and response schemas."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models.notification import NotificationType, NotificationStatus


class NotificationCreate(BaseModel):
    user_id: str = Field(..., description="알림을 받을 사용자 ID")
    notification_type: NotificationType
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    data: Optional[Dict[str, Any]] = None
    related_entity_type: Optional[str] = Field(None, max_length=50)
    related_entity_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationSendRequest(BaseModel):
    notification_type: NotificationType
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    data: Optional[Dict[str, Any]] = None
    related_entity_type: Optional[str] = Field(None, max_length=50)
    related_entity_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseModel):
    id: int
    user_id: str
    notification_type: NotificationType
    title: str
    body: str
    data: Optional[str]
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
    total: int
    notifications: list[NotificationResponse]
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


class NotificationStatsResponse(BaseModel):
    total_notifications: int
    unread_count: int
    failed_count: int
    read_count: int

    model_config = ConfigDict(from_attributes=True)


class NotificationMarkReadRequest(BaseModel):
    notification_ids: list[int] = Field(..., min_length=1)

    model_config = ConfigDict(from_attributes=True)


class NotificationMarkReadResponse(BaseModel):
    marked_count: int

    model_config = ConfigDict(from_attributes=True)


class FCMSendResult(BaseModel):
    success: bool
    message_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
