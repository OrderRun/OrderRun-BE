import logging
from typing import Optional, TYPE_CHECKING

from app.core.config import settings
from app.services.fcm_service import FCMService

if TYPE_CHECKING:
    from app.services.notification_worker import NotificationWorker

logger = logging.getLogger(__name__)

_fcm_service: Optional[FCMService] = None
_notification_worker: Optional["NotificationWorker"] = None


def get_fcm_service() -> FCMService:
    global _fcm_service
    if _fcm_service is None:
        _fcm_service = FCMService(
            credentials_path=settings.fcm_credentials_path,
            credentials_json=settings.fcm_credentials_json,
        )
    return _fcm_service


def get_notification_worker() -> "NotificationWorker":
    from app.services.notification_worker import NotificationWorker
    global _notification_worker
    if _notification_worker is None:
        _notification_worker = NotificationWorker(get_fcm_service())
    return _notification_worker


def init_fcm() -> None:
    service = get_fcm_service()
    if not service.initialized:
        logger.warning("FCM service failed to initialize — push notifications will be disabled")
    else:
        logger.info("FCM service initialized successfully")
