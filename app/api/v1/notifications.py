"""
Notification API endpoints for managing device tokens and notifications.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.errors import AppError, api_error
from app.core.security import get_current_user
from app.models.user import User
from app.models.notification import (
    DeviceToken,
    Notification,
    NotificationPreference,
    NotificationStatus
)
from app.schemas.notification import (
    DeviceTokenCreate,
    DeviceTokenResponse,
    DeviceTokenUpdate,
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationSendRequest
)
from app.services.fcm_service import FCMService
from app.services.notification_dispatcher import NotificationDispatcher
from app.core.config import settings
from datetime import datetime


router = APIRouter(prefix="/notifications", tags=["notifications"])


# Dependency for FCM service
def get_fcm_service() -> FCMService:
    """Get FCM service instance."""
    fcm_credentials_path = getattr(settings, 'FCM_CREDENTIALS_PATH', None)
    return FCMService(credentials_path=fcm_credentials_path)


# Dependency for notification dispatcher
def get_notification_dispatcher(
    fcm_service: FCMService = Depends(get_fcm_service)
) -> NotificationDispatcher:
    """Get notification dispatcher instance."""
    return NotificationDispatcher(fcm_service)


# ========== Device Token Endpoints ==========

@router.post(
    "/device-tokens",
    response_model=DeviceTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register device token for push notifications"
)
def register_device_token(
    token_data: DeviceTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DeviceToken:
    """
    Register a device token for the current user to receive push notifications.

    - **token**: FCM device token
    - **platform**: Device platform (ios, android, web)
    - **device_id**: Optional device identifier for tracking
    """
    # Check if token already exists
    existing_token = db.query(DeviceToken).filter(
        DeviceToken.token == token_data.token
    ).first()

    if existing_token:
        # Update existing token
        existing_token.user_id = current_user.id
        existing_token.platform = token_data.platform
        existing_token.device_id = token_data.device_id
        existing_token.is_active = True
        existing_token.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_token)
        return existing_token

    # Create new token
    device_token = DeviceToken(
        user_id=current_user.id,
        token=token_data.token,
        platform=token_data.platform,
        device_id=token_data.device_id,
        is_active=True
    )
    db.add(device_token)
    db.commit()
    db.refresh(device_token)
    return device_token


@router.get(
    "/device-tokens",
    response_model=List[DeviceTokenResponse],
    summary="Get all device tokens for current user"
)
def list_device_tokens(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[DeviceToken]:
    """Get all registered device tokens for the current user."""
    tokens = db.query(DeviceToken).filter(
        DeviceToken.user_id == current_user.id
    ).order_by(desc(DeviceToken.created_at)).all()
    return tokens


@router.patch(
    "/device-tokens/{token_id}",
    response_model=DeviceTokenResponse,
    summary="Update device token (e.g., deactivate)"
)
def update_device_token(
    token_id: int,
    token_update: DeviceTokenUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DeviceToken:
    """Update a device token (e.g., to deactivate it)."""
    device_token = db.query(DeviceToken).filter(
        DeviceToken.id == token_id,
        DeviceToken.user_id == current_user.id
    ).first()

    if not device_token:
        raise api_error(AppError.DEVICE_TOKEN_NOT_FOUND)

    if token_update.is_active is not None:
        device_token.is_active = token_update.is_active
        device_token.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(device_token)
    return device_token


@router.delete(
    "/device-tokens/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete device token"
)
def delete_device_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """Delete a device token."""
    device_token = db.query(DeviceToken).filter(
        DeviceToken.id == token_id,
        DeviceToken.user_id == current_user.id
    ).first()

    if not device_token:
        raise api_error(AppError.DEVICE_TOKEN_NOT_FOUND)

    db.delete(device_token)
    db.commit()


# ========== Notification Endpoints ==========

@router.get(
    "",
    response_model=NotificationListResponse,
    summary="Get notifications for current user"
)
def list_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    unread_only: bool = Query(False, description="Show only unread notifications"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> NotificationListResponse:
    """
    Get paginated list of notifications for the current user.

    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    - **unread_only**: Filter to show only unread notifications
    """
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )

    if unread_only:
        query = query.filter(Notification.read_at.is_(None))

    # Get total count
    total = query.count()

    # Get paginated results
    notifications = query.order_by(
        desc(Notification.created_at)
    ).offset((page - 1) * page_size).limit(page_size).all()

    return NotificationListResponse(
        total=total,
        notifications=notifications,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="Get a specific notification"
)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Notification:
    """Get details of a specific notification."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise api_error(AppError.NOTIFICATION_NOT_FOUND)

    return notification


@router.post(
    "/mark-read",
    status_code=status.HTTP_200_OK,
    summary="Mark notifications as read"
)
def mark_notifications_read(
    request: NotificationMarkReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Mark one or more notifications as read."""
    # Update notifications
    result = db.query(Notification).filter(
        Notification.id.in_(request.notification_ids),
        Notification.user_id == current_user.id,
        Notification.read_at.is_(None)  # Only update unread ones
    ).update(
        {
            Notification.read_at: datetime.utcnow(),
            Notification.status: NotificationStatus.READ
        },
        synchronize_session=False
    )

    db.commit()

    return {
        "success": True,
        "marked_count": result,
        "message": f"{result} notification(s) marked as read"
    }


@router.post(
    "/send",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a custom notification to current user (for testing)"
)
def send_notification(
    notification_request: NotificationSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    dispatcher: NotificationDispatcher = Depends(get_notification_dispatcher)
) -> Notification:
    """
    Send a custom notification to the current user.

    This endpoint is primarily for testing purposes.
    In production, notifications are typically triggered by business events.
    """
    dispatcher.send_custom_notification(
        db=db,
        user_id=current_user.id,
        title=notification_request.title,
        body=notification_request.body,
        data=notification_request.data,
        related_entity_type=notification_request.related_entity_type,
        related_entity_id=notification_request.related_entity_id
    )

    # Get the created notification
    notification = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at)).first()

    return notification


# ========== Notification Preference Endpoints ==========

@router.get(
    "/preferences/me",
    response_model=NotificationPreferenceResponse,
    summary="Get notification preferences for current user"
)
def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> NotificationPreference:
    """Get notification preferences for the current user."""
    preference = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()

    # Create default preferences if none exist
    if not preference:
        preference = NotificationPreference(user_id=current_user.id)
        db.add(preference)
        db.commit()
        db.refresh(preference)

    return preference


@router.patch(
    "/preferences/me",
    response_model=NotificationPreferenceResponse,
    summary="Update notification preferences"
)
def update_notification_preferences(
    preference_update: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> NotificationPreference:
    """Update notification preferences for the current user."""
    preference = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()

    # Create if doesn't exist
    if not preference:
        preference = NotificationPreference(user_id=current_user.id)
        db.add(preference)

    # Update fields
    update_data = preference_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preference, field, value)

    preference.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(preference)
    return preference


# ========== Stats Endpoint ==========

@router.get(
    "/stats/me",
    summary="Get notification statistics for current user"
)
def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Get notification statistics for the current user."""
    total = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).count()

    unread = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read_at.is_(None)
    ).count()

    failed = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.status == NotificationStatus.FAILED
    ).count()

    return {
        "total_notifications": total,
        "unread_count": unread,
        "failed_count": failed,
        "read_count": total - unread
    }
