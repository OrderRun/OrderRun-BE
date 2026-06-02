"""Firebase Cloud Messaging (FCM) service for sending push notifications."""
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("firebase-admin package not installed. FCM functionality will be disabled.")

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationStatus, NotificationType
from app.models.user import UserFCMToken
from app.schemas.notification import FCMSendResult


logger = logging.getLogger(__name__)


class FCMService:
    def __init__(self, credentials_path: Optional[str] = None):
        self.initialized = False
        self.credentials_path = credentials_path

        if not FIREBASE_AVAILABLE:
            logger.error("Firebase Admin SDK not available. Install with: pip install firebase-admin")
            return

        try:
            if not firebase_admin._apps:
                if credentials_path:
                    cred = credentials.Certificate(credentials_path)
                    firebase_admin.initialize_app(cred)
                else:
                    firebase_admin.initialize_app()
                logger.info("Firebase Admin SDK initialized successfully")
            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
            self.initialized = False

    def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image: Optional[str] = None,
        priority: str = "high",
    ) -> FCMSendResult:
        if not self.initialized:
            return FCMSendResult(success=False, error_code="NOT_INITIALIZED", error_message="FCM service not initialized")

        try:
            notification = messaging.Notification(title=title, body=body, image=image)
            android_config = messaging.AndroidConfig(
                priority=priority,
                notification=messaging.AndroidNotification(
                    sound="default",
                    notification_priority="PRIORITY_HIGH" if priority == "high" else "PRIORITY_DEFAULT",
                ),
            )
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound="default", badge=1, content_available=True)
                )
            )
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
                android=android_config,
                apns=apns_config,
            )
            response = messaging.send(message)
            logger.info(f"Successfully sent message to token {token[:20]}... Message ID: {response}")
            return FCMSendResult(success=True, message_id=response)

        except messaging.UnregisteredError:
            logger.warning(f"Token is unregistered: {token[:20]}...")
            return FCMSendResult(success=False, error_code="UNREGISTERED", error_message="Device token is no longer valid")
        except messaging.InvalidArgumentError as e:
            logger.error(f"Invalid argument when sending to {token[:20]}...: {str(e)}")
            return FCMSendResult(success=False, error_code="INVALID_ARGUMENT", error_message=str(e))
        except messaging.SenderIdMismatchError:
            logger.error(f"Sender ID mismatch for token {token[:20]}...")
            return FCMSendResult(success=False, error_code="SENDER_ID_MISMATCH", error_message="Token is not registered for this sender")
        except Exception as e:
            logger.error(f"Unexpected error sending to {token[:20]}...: {str(e)}")
            return FCMSendResult(success=False, error_code="UNKNOWN", error_message=str(e))

    def send_to_user(
        self,
        db: Session,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[int] = None,
        image: Optional[str] = None,
    ) -> tuple[Notification, FCMSendResult]:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            data=json.dumps(data) if data else None,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            status=NotificationStatus.PENDING,
        )
        db.add(notification)
        db.flush()

        token_record = db.query(UserFCMToken).filter(UserFCMToken.user_id == user_id).first()

        if not token_record:
            logger.warning(f"No FCM token found for user {user_id}")
            notification.status = NotificationStatus.FAILED
            notification.error_message = "No FCM token registered"
            db.commit()
            return notification, FCMSendResult(success=False, error_code="NO_TOKEN", error_message="No FCM token registered")

        fcm_data: Dict[str, str] = {
            "notification_id": str(notification.id),
            "notification_type": notification_type.value,
        }
        if related_entity_type:
            fcm_data["related_entity_type"] = related_entity_type
        if related_entity_id:
            fcm_data["related_entity_id"] = str(related_entity_id)
        if data:
            for key, value in data.items():
                fcm_data[f"data_{key}"] = str(value)

        result = self.send_notification(
            token=token_record.fcm_token,
            title=title,
            body=body,
            data=fcm_data,
            image=image,
        )

        if result.success:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            if result.message_id:
                notification.fcm_message_id = result.message_id
        else:
            notification.status = NotificationStatus.FAILED
            notification.error_message = result.error_message

        db.commit()
        db.refresh(notification)

        logger.info(f"Notification {notification.id} sent to user {user_id}: {'success' if result.success else 'failed'}")
        return notification, result

    def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image: Optional[str] = None,
    ) -> FCMSendResult:
        if not self.initialized:
            return FCMSendResult(success=False, error_code="NOT_INITIALIZED", error_message="FCM service not initialized")

        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body, image=image),
                data=data or {},
                topic=topic,
            )
            response = messaging.send(message)
            logger.info(f"Successfully sent message to topic '{topic}'. Message ID: {response}")
            return FCMSendResult(success=True, message_id=response)
        except Exception as e:
            logger.error(f"Error sending to topic '{topic}': {str(e)}")
            return FCMSendResult(success=False, error_code="TOPIC_SEND_FAILED", error_message=str(e))
