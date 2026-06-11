"""Notification query and command service layer."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import AppError, api_error
from app.core.time import utcnow_naive
from app.models.notification import Notification, NotificationStatus
from app.schemas.notification import (
    NotificationListResponse,
    NotificationMarkReadResponse,
    NotificationResponse,
    NotificationSendRequest,
    NotificationStatsResponse,
)
from app.services.notification_dispatcher import NotificationDispatcher


class NotificationService:
    """Service layer for Notification API queries and commands."""

    @staticmethod
    def list_notifications(
        db: Session,
        user_id: str,
        page: int,
        page_size: int,
        unread_only: bool,
    ) -> NotificationListResponse:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.read_at.is_(None))

        total = query.count()
        notifications = (
            query.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return NotificationListResponse(
            total=total,
            notifications=notifications,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def get_notification_stats(db: Session, user_id: str) -> NotificationStatsResponse:
        total = db.query(Notification).filter(Notification.user_id == user_id).count()
        unread = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.read_at.is_(None))
            .count()
        )
        failed = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.status == NotificationStatus.FAILED,
            )
            .count()
        )
        return NotificationStatsResponse(
            total_notifications=total,
            unread_count=unread,
            failed_count=failed,
            read_count=total - unread,
        )

    @staticmethod
    def get_notification(db: Session, user_id: str, notification_id: int) -> NotificationResponse:
        notification = (
            db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .first()
        )
        if notification is None:
            raise api_error(AppError.NOTIFICATION_NOT_FOUND)
        return NotificationResponse.model_validate(notification)

    @staticmethod
    def mark_notifications_read(
        db: Session,
        user_id: str,
        notification_ids: list[int],
    ) -> NotificationMarkReadResponse:
        marked_count = (
            db.query(Notification)
            .filter(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            .update(
                {
                    Notification.read_at: utcnow_naive(),
                    Notification.status: NotificationStatus.READ,
                },
                synchronize_session=False,
            )
        )
        db.commit()
        return NotificationMarkReadResponse(marked_count=marked_count)

    @staticmethod
    def send_custom_notification(
        db: Session,
        user_id: str,
        request: NotificationSendRequest,
        dispatcher: NotificationDispatcher,
    ) -> NotificationResponse:
        notification = dispatcher.send_custom_notification(
            db=db,
            user_id=user_id,
            title=request.title,
            body=request.body,
            data=request.data,
            related_entity_type=request.related_entity_type,
            related_entity_id=request.related_entity_id,
        )
        return NotificationResponse.model_validate(notification)
