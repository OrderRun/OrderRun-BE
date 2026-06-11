"""Push notification API endpoints."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from app.core.database import get_db
from app.core.errors import AppError, api_error
from app.core.openapi import (
    NOTIFICATION_LIST_EXAMPLE,
    NOTIFICATION_MARK_READ_EXAMPLE,
    NOTIFICATION_RESPONSE_EXAMPLE,
    NOTIFICATION_STATS_EXAMPLE,
    error_responses,
    success_response,
)
from app.core.security import get_current_user
from app.core.firebase import get_fcm_service
from app.models.user import User
from app.models.notification import Notification, NotificationStatus
from app.schemas.common import ApiResponse
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkReadResponse,
    NotificationMarkReadRequest,
    NotificationSendRequest,
    NotificationStatsResponse,
)
from app.services.notification_dispatcher import NotificationDispatcher


router = APIRouter(prefix="/notifications", tags=["알림"])


def get_notification_dispatcher() -> NotificationDispatcher:
    return NotificationDispatcher(get_fcm_service())


@router.get(
    "",
    response_model=ApiResponse[NotificationListResponse],
    summary="알림 목록 조회",
    description="현재 사용자의 알림 목록을 페이지 단위로 조회합니다.",
    responses={
        200: success_response(NOTIFICATION_LIST_EXAMPLE),
        **error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR),
    },
)
def list_notifications(
    page: int = Query(1, ge=1, description="페이지 번호(1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    unread_only: bool = Query(False, description="읽지 않은 알림만 조회"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[NotificationListResponse]:
    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if unread_only:
        query = query.filter(Notification.read_at.is_(None))

    total = query.count()
    notifications = query.order_by(desc(Notification.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    data = NotificationListResponse(total=total, notifications=notifications, page=page, page_size=page_size)
    return ApiResponse(success=True, data=data)


@router.get(
    "/stats/me",
    response_model=ApiResponse[NotificationStatsResponse],
    summary="알림 통계 조회",
    responses={
        200: success_response(NOTIFICATION_STATS_EXAMPLE),
        **error_responses(AppError.INVALID_TOKEN),
    },
)
def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[NotificationStatsResponse]:
    total = db.query(Notification).filter(Notification.user_id == current_user.id).count()
    unread = db.query(Notification).filter(Notification.user_id == current_user.id, Notification.read_at.is_(None)).count()
    failed = db.query(Notification).filter(Notification.user_id == current_user.id, Notification.status == NotificationStatus.FAILED).count()

    data = NotificationStatsResponse(
        total_notifications=total,
        unread_count=unread,
        failed_count=failed,
        read_count=total - unread,
    )
    return ApiResponse(success=True, data=data)


@router.get(
    "/{notification_id}",
    response_model=ApiResponse[NotificationResponse],
    summary="알림 상세 조회",
    responses={
        200: success_response(NOTIFICATION_RESPONSE_EXAMPLE),
        **error_responses(AppError.INVALID_TOKEN, AppError.NOTIFICATION_NOT_FOUND),
    },
)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[NotificationResponse]:
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()

    if not notification:
        raise api_error(AppError.NOTIFICATION_NOT_FOUND)

    return ApiResponse(success=True, data=notification)


@router.post(
    "/mark-read",
    response_model=ApiResponse[NotificationMarkReadResponse],
    status_code=status.HTTP_200_OK,
    summary="알림 읽음 처리",
    responses={
        200: success_response(NOTIFICATION_MARK_READ_EXAMPLE),
        **error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR),
    },
)
def mark_notifications_read(
    request: NotificationMarkReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[NotificationMarkReadResponse]:
    result = db.query(Notification).filter(
        Notification.id.in_(request.notification_ids),
        Notification.user_id == current_user.id,
        Notification.read_at.is_(None),
    ).update(
        {Notification.read_at: datetime.utcnow(), Notification.status: NotificationStatus.READ},
        synchronize_session=False,
    )
    db.commit()

    return ApiResponse(
        success=True,
        data=NotificationMarkReadResponse(marked_count=result),
        message=f"{result} notification(s) marked as read",
    )


@router.post(
    "/send",
    response_model=ApiResponse[NotificationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="테스트 알림 발송",
    description="현재 사용자에게 테스트용 커스텀 알림을 발송합니다.",
    responses={
        201: success_response(NOTIFICATION_RESPONSE_EXAMPLE),
        **error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR),
    },
)
def send_notification(
    notification_request: NotificationSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    dispatcher: NotificationDispatcher = Depends(get_notification_dispatcher),
) -> ApiResponse[NotificationResponse]:
    dispatcher.send_custom_notification(
        db=db,
        user_id=current_user.id,
        title=notification_request.title,
        body=notification_request.body,
        data=notification_request.data,
        related_entity_type=notification_request.related_entity_type,
        related_entity_id=notification_request.related_entity_id,
    )

    notification = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at)).first()

    return ApiResponse(success=True, data=notification)
