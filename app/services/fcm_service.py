"""
Firebase Cloud Messaging (FCM) service for sending push notifications.

This module provides a centralized service for:
- Initializing Firebase Admin SDK
- Sending push notifications to individual devices
- Sending push notifications to multiple devices
- Managing notification delivery status
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("firebase-admin package not installed. FCM functionality will be disabled.")

from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    DeviceToken,
    NotificationStatus,
    NotificationType
)
from app.schemas.notification import FCMSendResult


logger = logging.getLogger(__name__)


class FCMService:
    """
    Service for sending Firebase Cloud Messaging notifications.

    This service handles:
    - Firebase Admin SDK initialization
    - Notification construction and sending
    - Delivery status tracking
    - Error handling and retry logic
    """

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize FCM service.

        Args:
            credentials_path: Path to Firebase service account JSON file.
                            If None, will attempt to use default credentials.
        """
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
                    # Try to initialize with default credentials
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
        priority: str = "high"
    ) -> FCMSendResult:
        """
        Send a push notification to a single device.

        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Optional data payload (must be string key-value pairs)
            image: Optional image URL
            priority: Message priority ('high' or 'normal')

        Returns:
            FCMSendResult with success status and message ID or error details
        """
        if not self.initialized:
            return FCMSendResult(
                success=False,
                error_code="NOT_INITIALIZED",
                error_message="FCM service not initialized"
            )

        try:
            # Build notification payload
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image
            )

            # Build Android-specific config
            android_config = messaging.AndroidConfig(
                priority=priority,
                notification=messaging.AndroidNotification(
                    sound="default",
                    notification_priority="PRIORITY_HIGH" if priority == "high" else "PRIORITY_DEFAULT"
                )
            )

            # Build APNs (iOS) config
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound="default",
                        badge=1,
                        content_available=True
                    )
                )
            )

            # Create message
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
                android=android_config,
                apns=apns_config
            )

            # Send message
            response = messaging.send(message)
            logger.info(f"Successfully sent message to token {token[:20]}... Message ID: {response}")

            return FCMSendResult(
                success=True,
                message_id=response
            )

        except messaging.UnregisteredError:
            logger.warning(f"Token is unregistered: {token[:20]}...")
            return FCMSendResult(
                success=False,
                error_code="UNREGISTERED",
                error_message="Device token is no longer valid"
            )
        except messaging.InvalidArgumentError as e:
            logger.error(f"Invalid argument when sending to {token[:20]}...: {str(e)}")
            return FCMSendResult(
                success=False,
                error_code="INVALID_ARGUMENT",
                error_message=str(e)
            )
        except messaging.SenderIdMismatchError:
            logger.error(f"Sender ID mismatch for token {token[:20]}...")
            return FCMSendResult(
                success=False,
                error_code="SENDER_ID_MISMATCH",
                error_message="Token is not registered for this sender"
            )
        except Exception as e:
            logger.error(f"Unexpected error sending to {token[:20]}...: {str(e)}")
            return FCMSendResult(
                success=False,
                error_code="UNKNOWN",
                error_message=str(e)
            )

    def send_multicast(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image: Optional[str] = None,
        priority: str = "high"
    ) -> Dict[str, Any]:
        """
        Send a push notification to multiple devices.

        Args:
            tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Optional data payload
            image: Optional image URL
            priority: Message priority

        Returns:
            Dictionary with success/failure counts and individual results
        """
        if not self.initialized:
            return {
                "success": False,
                "error": "FCM service not initialized",
                "success_count": 0,
                "failure_count": len(tokens)
            }

        if not tokens:
            return {
                "success": True,
                "success_count": 0,
                "failure_count": 0,
                "responses": []
            }

        try:
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image
            )

            # Build multicast message
            message = messaging.MulticastMessage(
                notification=notification,
                data=data or {},
                tokens=tokens,
                android=messaging.AndroidConfig(priority=priority),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound="default", badge=1)
                    )
                )
            )

            # Send multicast
            response = messaging.send_multicast(message)

            logger.info(
                f"Multicast sent: {response.success_count} successful, "
                f"{response.failure_count} failed out of {len(tokens)} tokens"
            )

            # Parse individual responses
            results = []
            for idx, resp in enumerate(response.responses):
                if resp.success:
                    results.append({
                        "token": tokens[idx],
                        "success": True,
                        "message_id": resp.message_id
                    })
                else:
                    results.append({
                        "token": tokens[idx],
                        "success": False,
                        "error_code": resp.exception.__class__.__name__ if resp.exception else "UNKNOWN",
                        "error_message": str(resp.exception) if resp.exception else "Unknown error"
                    })

            return {
                "success": True,
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "responses": results
            }

        except Exception as e:
            logger.error(f"Error sending multicast: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "success_count": 0,
                "failure_count": len(tokens)
            }

    def send_to_user(
        self,
        db: Session,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[int] = None,
        image: Optional[str] = None
    ) -> tuple[Notification, List[FCMSendResult]]:
        """
        Send notification to all active devices of a user.

        This method:
        1. Creates a notification record in the database
        2. Fetches all active device tokens for the user
        3. Sends FCM messages to all devices
        4. Updates notification status based on results

        Args:
            db: Database session
            user_id: User ID to send to
            notification_type: Type of notification
            title: Notification title
            body: Notification body
            data: Optional data payload
            related_entity_type: Related entity type (e.g., 'proposal')
            related_entity_id: Related entity ID
            image: Optional notification image

        Returns:
            Tuple of (Notification record, List of FCMSendResults)
        """
        # Create notification record
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            data=json.dumps(data) if data else None,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            status=NotificationStatus.PENDING
        )
        db.add(notification)
        db.flush()  # Get notification ID

        # Get all active device tokens for user
        device_tokens = db.query(DeviceToken).filter(
            DeviceToken.user_id == user_id,
            DeviceToken.is_active == True
        ).all()

        if not device_tokens:
            logger.warning(f"No active device tokens found for user {user_id}")
            notification.status = NotificationStatus.FAILED
            notification.error_message = "No active device tokens"
            db.commit()
            return notification, []

        # Prepare data payload for FCM
        fcm_data = {
            "notification_id": str(notification.id),
            "notification_type": notification_type.value,
        }
        if related_entity_type:
            fcm_data["related_entity_type"] = related_entity_type
        if related_entity_id:
            fcm_data["related_entity_id"] = str(related_entity_id)
        if data:
            # Add custom data fields (flatten dict to string values)
            for key, value in data.items():
                fcm_data[f"data_{key}"] = str(value)

        # Send to all devices
        results = []
        success_count = 0
        tokens = [dt.token for dt in device_tokens]

        # Send multicast for efficiency
        if len(tokens) > 1:
            multicast_result = self.send_multicast(
                tokens=tokens,
                title=title,
                body=body,
                data=fcm_data,
                image=image
            )

            if multicast_result.get("success"):
                success_count = multicast_result.get("success_count", 0)
                # Convert to FCMSendResult format
                for resp in multicast_result.get("responses", []):
                    results.append(FCMSendResult(
                        success=resp.get("success", False),
                        message_id=resp.get("message_id"),
                        error_code=resp.get("error_code"),
                        error_message=resp.get("error_message")
                    ))
        else:
            # Single device
            result = self.send_notification(
                token=tokens[0],
                title=title,
                body=body,
                data=fcm_data,
                image=image
            )
            results.append(result)
            if result.success:
                success_count = 1

        # Update notification status
        if success_count > 0:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            if results and results[0].message_id:
                notification.fcm_message_id = results[0].message_id
        else:
            notification.status = NotificationStatus.FAILED
            error_messages = [r.error_message for r in results if r.error_message]
            notification.error_message = "; ".join(error_messages) if error_messages else "All devices failed"

        # Update device token last_used_at for successful sends
        for idx, result in enumerate(results):
            if result.success and idx < len(device_tokens):
                device_tokens[idx].last_used_at = datetime.utcnow()

        db.commit()
        db.refresh(notification)

        logger.info(
            f"Notification {notification.id} sent to user {user_id}: "
            f"{success_count}/{len(device_tokens)} devices successful"
        )

        return notification, results

    def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image: Optional[str] = None
    ) -> FCMSendResult:
        """
        Send notification to a topic (for broadcast messages).

        Args:
            topic: Topic name
            title: Notification title
            body: Notification body
            data: Optional data payload
            image: Optional image URL

        Returns:
            FCMSendResult
        """
        if not self.initialized:
            return FCMSendResult(
                success=False,
                error_code="NOT_INITIALIZED",
                error_message="FCM service not initialized"
            )

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image
                ),
                data=data or {},
                topic=topic
            )

            response = messaging.send(message)
            logger.info(f"Successfully sent message to topic '{topic}'. Message ID: {response}")

            return FCMSendResult(
                success=True,
                message_id=response
            )

        except Exception as e:
            logger.error(f"Error sending to topic '{topic}': {str(e)}")
            return FCMSendResult(
                success=False,
                error_code="TOPIC_SEND_FAILED",
                error_message=str(e)
            )
