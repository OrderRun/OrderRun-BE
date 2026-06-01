"""Push notification API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.errors import AppError, api_error
from app.core.openapi import AUTH_ERROR_RESPONSES, error_responses
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


router = APIRouter(prefix="/notifications", tags=["알림"])


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
    summary="디바이스 토큰 등록",
    description="현재 사용자의 푸시 알림 수신용 FCM 디바이스 토큰을 등록합니다.",
    responses=error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR),
)
def register_device_token(
    token_data: DeviceTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DeviceToken:
    """현재 사용자의 FCM 디바이스 토큰을 등록합니다."""
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
    summary="디바이스 토큰 목록 조회",
    description="현재 사용자에게 등록된 모든 디바이스 토큰을 조회합니다.",
    responses=AUTH_ERROR_RESPONSES,
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
    summary="디바이스 토큰 수정",
    description="디바이스 토큰의 활성 상태를 수정합니다.",
    responses=error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR, AppError.DEVICE_TOKEN_NOT_FOUND),
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
    summary="디바이스 토큰 삭제",
    description="현재 사용자에게 등록된 디바이스 토큰을 삭제합니다.",
    responses=error_responses(AppError.INVALID_TOKEN, AppError.DEVICE_TOKEN_NOT_FOUND),
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
    summary="알림 목록 조회",
    description="현재 사용자의 알림 목록을 페이지 단위로 조회합니다.",
    responses=AUTH_ERROR_RESPONSES,
)
def list_notifications(
    page: int = Query(1, ge=1, description="페이지 번호(1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    unread_only: bool = Query(False, description="읽지 않은 알림만 조회할지 여부"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> NotificationListResponse:
    """현재 사용자의 알림 목록을 조회합니다."""
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
    summary="알림 상세 조회",
    description="알림 ID로 알림 상세 정보를 조회합니다.",
    responses=error_responses(AppError.INVALID_TOKEN, AppError.NOTIFICATION_NOT_FOUND),
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
    summary="알림 읽음 처리",
    description="하나 이상의 알림을 읽음 상태로 변경합니다.",
    responses=error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR),
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
    summary="테스트 알림 발송",
    description="현재 사용자에게 테스트용 커스텀 알림을 발송합니다.",
    responses=error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR),
)
def send_notification(
    notification_request: NotificationSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    dispatcher: NotificationDispatcher = Depends(get_notification_dispatcher)
) -> Notification:
    """현재 사용자에게 테스트용 알림을 발송합니다."""
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
    summary="알림 설정 조회",
    description="현재 사용자의 알림 수신 설정을 조회합니다.",
    responses=AUTH_ERROR_RESPONSES,
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
    summary="알림 설정 수정",
    description="현재 사용자의 알림 수신 설정을 수정합니다.",
    responses=error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR),
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
    summary="알림 통계 조회",
    description="현재 사용자의 전체/읽지 않음/실패/읽음 알림 수를 조회합니다.",
    responses=AUTH_ERROR_RESPONSES,
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
