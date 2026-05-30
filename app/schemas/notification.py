"""
Pydantic schemas for notification-related request/response models.
"""
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
    token: str = Field(..., min_length=1, max_length=255, description="FCM device token")
    platform: DevicePlatform = Field(..., description="Device platform (ios, android, web)")
    device_id: Optional[str] = Field(None, max_length=255, description="Optional device identifier")

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
    is_active: Optional[bool] = Field(None, description="Set to false to deactivate token")

    model_config = ConfigDict(from_attributes=True)


# ========== Notification Schemas ==========

class NotificationCreate(BaseModel):
    """Schema for creating a notification (internal use)."""
    user_id: str = Field(..., description="User ID to send notification to")
    notification_type: NotificationType = Field(..., description="Type of notification")
    title: str = Field(..., min_length=1, max_length=255, description="Notification title")
    body: str = Field(..., min_length=1, description="Notification body")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional payload data")
    related_entity_type: Optional[str] = Field(None, max_length=50, description="Related entity type (e.g., 'proposal', 'offer')")
    related_entity_id: Optional[int] = Field(None, description="Related entity ID")

    model_config = ConfigDict(from_attributes=True)


class NotificationSendRequest(BaseModel):
    """Schema for sending a notification via API."""
    notification_type: NotificationType = Field(..., description="Type of notification")
    title: str = Field(..., min_length=1, max_length=255, description="Notification title")
    body: str = Field(..., min_length=1, description="Notification body")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional payload data")
    related_entity_type: Optional[str] = Field(None, max_length=50, description="Related entity type")
    related_entity_id: Optional[int] = Field(None, description="Related entity ID")

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
    notification_ids: list[int] = Field(..., min_length=1, description="List of notification IDs to mark as read")

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
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23, description="Quiet hours start (0-23)")
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23, description="Quiet hours end (0-23)")

    model_config = ConfigDict(from_attributes=True)


# ========== FCM Specific Schemas ==========

class FCMNotificationPayload(BaseModel):
    """Schema for FCM notification payload."""
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    image: Optional[str] = Field(None, description="Optional notification image URL")

    model_config = ConfigDict(from_attributes=True)


class FCMDataPayload(BaseModel):
    """Schema for FCM data payload."""
    notification_id: str = Field(..., description="Internal notification ID")
    notification_type: str = Field(..., description="Type of notification")
    related_entity_type: Optional[str] = Field(None, description="Related entity type")
    related_entity_id: Optional[str] = Field(None, description="Related entity ID")
    custom_data: Optional[Dict[str, str]] = Field(None, description="Additional custom data")

    model_config = ConfigDict(from_attributes=True)


class FCMSendResult(BaseModel):
    """Schema for FCM send result."""
    success: bool = Field(..., description="Whether the send was successful")
    message_id: Optional[str] = Field(None, description="FCM message ID if successful")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    model_config = ConfigDict(from_attributes=True)
