"""Notification Outbox worker — sends PENDING notifications via FCM, retries FAILED."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationStatus
from app.services.fcm_service import FCMService

logger = logging.getLogger(__name__)

_MAX_RETRY = 3


class NotificationWorker:
    def __init__(self, fcm_service: FCMService) -> None:
        self.fcm_service = fcm_service

    def flush_pending(self, db_factory: Callable[[], Session]) -> None:
        """PENDING 알림을 FCM으로 발송한다. BackgroundTask 또는 스케줄러에서 호출."""
        with db_factory() as db:
            self._send_batch(db, NotificationStatus.PENDING)

    def retry_failed(self, db_factory: Callable[[], Session]) -> None:
        """FAILED 알림 중 retry_count < MAX_RETRY 인 것을 재발송한다."""
        with db_factory() as db:
            self._send_batch(db, NotificationStatus.FAILED, only_retryable=True)

    def _send_batch(self, db: Session, status: NotificationStatus, only_retryable: bool = False) -> None:
        import json

        query = db.query(Notification).filter(Notification.status == status)
        if only_retryable:
            query = query.filter(Notification.retry_count < _MAX_RETRY)

        notifications = query.order_by(Notification.created_at).limit(100).all()
        if not notifications:
            return

        logger.info("Sending %d %s notifications", len(notifications), status.value)

        for notif in notifications:
            notification_type = getattr(notif.notification_type, "value", notif.notification_type)
            data: dict[str, str] = {
                "notification_id": str(notif.id),
                "notification_type": str(notification_type),
            }
            if notif.related_entity_type:
                data["related_entity_type"] = notif.related_entity_type
            if notif.related_entity_id:
                data["related_entity_id"] = str(notif.related_entity_id)
            if notif.data:
                for k, v in json.loads(notif.data).items():
                    data[f"extra_{k}"] = str(v)

            result = self.fcm_service.send_notification(
                token=self._get_token(db, notif.user_id),
                title=notif.title,
                body=notif.body,
                data=data,
            ) if self._get_token(db, notif.user_id) else None

            if result is None or not result.success:
                notif.status = NotificationStatus.FAILED
                notif.retry_count = (notif.retry_count or 0) + 1
                notif.error_message = result.error_message if result else "No FCM token"
            else:
                notif.status = NotificationStatus.SENT
                notif.sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
                notif.fcm_message_id = result.message_id

        db.commit()

    @staticmethod
    def _get_token(db: Session, user_id: str) -> str | None:
        from app.models.user import UserFCMToken
        record = db.query(UserFCMToken).filter(UserFCMToken.user_id == user_id).first()
        return record.fcm_token if record else None
