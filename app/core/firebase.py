import logging
from typing import Optional

from app.core.config import settings
from app.services.fcm_service import FCMService

logger = logging.getLogger(__name__)

_fcm_service: Optional[FCMService] = None


def get_fcm_service() -> FCMService:
    global _fcm_service
    if _fcm_service is None:
        _fcm_service = FCMService(
            credentials_path=settings.fcm_credentials_path,
            credentials_json=settings.fcm_credentials_json,
        )
    return _fcm_service


def init_fcm() -> None:
    service = get_fcm_service()
    if not service.initialized:
        logger.warning("FCM service failed to initialize — push notifications will be disabled")
    else:
        logger.info("FCM service initialized successfully")
