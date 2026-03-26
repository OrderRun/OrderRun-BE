"""
Notification Event Dispatcher

This module provides a centralized notification dispatcher that can be called
from any API endpoint or service to trigger notifications based on business events.

Design pattern: Event-driven notification system
- Services/APIs emit events (e.g., "proposal_created", "offer_accepted")
- Dispatcher handles notification logic and FCM delivery
- Decouples business logic from notification concerns
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.notification import NotificationType, NotificationPreference
from app.services.fcm_service import FCMService


logger = logging.getLogger(__name__)


class NotificationDispatcher:
    """
    Centralized notification dispatcher for handling business events.

    Usage example:
        dispatcher = NotificationDispatcher(fcm_service)
        dispatcher.notify_proposal_created(db, proposal_id, customer_id)
    """

    def __init__(self, fcm_service: FCMService):
        """
        Initialize dispatcher with FCM service.

        Args:
            fcm_service: Initialized FCM service instance
        """
        self.fcm_service = fcm_service

    def _should_send_notification(
        self,
        db: Session,
        user_id: int,
        notification_type: NotificationType
    ) -> bool:
        """
        Check if user preferences allow this notification type.

        Args:
            db: Database session
            user_id: User ID
            notification_type: Type of notification

        Returns:
            True if notification should be sent, False otherwise
        """
        # Get user preferences
        preference = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

        # If no preference exists, allow all notifications (opt-in by default)
        if not preference:
            return True

        # Check preference based on notification type
        type_to_preference = {
            NotificationType.PROPOSAL_NEW: preference.enable_proposal_notifications,
            NotificationType.PROPOSAL_MATCHED: preference.enable_proposal_notifications,
            NotificationType.PROPOSAL_CANCELLED: preference.enable_proposal_notifications,
            NotificationType.OFFER_NEW: preference.enable_offer_notifications,
            NotificationType.OFFER_ACCEPTED: preference.enable_offer_notifications,
            NotificationType.OFFER_REJECTED: preference.enable_offer_notifications,
            NotificationType.MISSION_STARTED: preference.enable_mission_notifications,
            NotificationType.MISSION_COMPLETED: preference.enable_mission_notifications,
            NotificationType.PAYMENT_COMPLETED: preference.enable_payment_notifications,
            NotificationType.PAYMENT_FAILED: preference.enable_payment_notifications,
            NotificationType.SYSTEM_ANNOUNCEMENT: preference.enable_system_notifications,
        }

        return type_to_preference.get(notification_type, True)

    # ========== Proposal Events ==========

    def notify_proposal_created(
        self,
        db: Session,
        proposal_id: int,
        creator_id: int,
        proposal_title: str
    ) -> None:
        """
        Notify when a new proposal is created.

        This could notify nearby runners or subscribed users.

        Args:
            db: Database session
            proposal_id: Created proposal ID
            creator_id: User who created the proposal
            proposal_title: Title of the proposal
        """
        # This is a placeholder - in real implementation, you would:
        # 1. Find eligible runners (e.g., based on location)
        # 2. Send notifications to them
        logger.info(f"Proposal {proposal_id} created by user {creator_id}: {proposal_title}")
        # Implementation depends on your business logic

    def notify_proposal_matched(
        self,
        db: Session,
        proposal_id: int,
        customer_id: int,
        runner_id: int,
        proposal_title: str
    ) -> None:
        """
        Notify customer and runner when a proposal is matched.

        Args:
            db: Database session
            proposal_id: Matched proposal ID
            customer_id: Customer user ID
            runner_id: Runner user ID
            proposal_title: Title of the proposal
        """
        # Notify customer
        if self._should_send_notification(db, customer_id, NotificationType.PROPOSAL_MATCHED):
            self.fcm_service.send_to_user(
                db=db,
                user_id=customer_id,
                notification_type=NotificationType.PROPOSAL_MATCHED,
                title="의뢰가 매칭되었습니다!",
                body=f"'{proposal_title}' 의뢰에 러너가 배정되었습니다.",
                related_entity_type="proposal",
                related_entity_id=proposal_id,
                data={"proposal_id": proposal_id, "runner_id": runner_id}
            )

        # Notify runner
        if self._should_send_notification(db, runner_id, NotificationType.PROPOSAL_MATCHED):
            self.fcm_service.send_to_user(
                db=db,
                user_id=runner_id,
                notification_type=NotificationType.PROPOSAL_MATCHED,
                title="새로운 미션이 배정되었습니다!",
                body=f"'{proposal_title}' 미션을 시작하세요.",
                related_entity_type="proposal",
                related_entity_id=proposal_id,
                data={"proposal_id": proposal_id, "customer_id": customer_id}
            )

    def notify_proposal_cancelled(
        self,
        db: Session,
        proposal_id: int,
        affected_user_ids: list[int],
        proposal_title: str,
        reason: Optional[str] = None
    ) -> None:
        """
        Notify affected users when a proposal is cancelled.

        Args:
            db: Database session
            proposal_id: Cancelled proposal ID
            affected_user_ids: List of user IDs to notify
            proposal_title: Title of the proposal
            reason: Optional cancellation reason
        """
        body = f"'{proposal_title}' 의뢰가 취소되었습니다."
        if reason:
            body += f" 사유: {reason}"

        for user_id in affected_user_ids:
            if self._should_send_notification(db, user_id, NotificationType.PROPOSAL_CANCELLED):
                self.fcm_service.send_to_user(
                    db=db,
                    user_id=user_id,
                    notification_type=NotificationType.PROPOSAL_CANCELLED,
                    title="의뢰가 취소되었습니다",
                    body=body,
                    related_entity_type="proposal",
                    related_entity_id=proposal_id,
                    data={"proposal_id": proposal_id, "reason": reason or ""}
                )

    # ========== Offer Events ==========

    def notify_offer_received(
        self,
        db: Session,
        offer_id: int,
        proposal_id: int,
        customer_id: int,
        runner_id: int,
        proposal_title: str,
        offer_amount: int
    ) -> None:
        """
        Notify customer when they receive a new offer.

        Args:
            db: Database session
            offer_id: Offer ID
            proposal_id: Related proposal ID
            customer_id: Customer user ID
            runner_id: Runner user ID
            proposal_title: Title of the proposal
            offer_amount: Offer amount
        """
        if self._should_send_notification(db, customer_id, NotificationType.OFFER_NEW):
            self.fcm_service.send_to_user(
                db=db,
                user_id=customer_id,
                notification_type=NotificationType.OFFER_NEW,
                title="새로운 제안이 도착했습니다!",
                body=f"'{proposal_title}' 의뢰에 {offer_amount:,}원의 제안이 왔습니다.",
                related_entity_type="offer",
                related_entity_id=offer_id,
                data={
                    "offer_id": offer_id,
                    "proposal_id": proposal_id,
                    "runner_id": runner_id,
                    "amount": str(offer_amount)
                }
            )

    def notify_offer_accepted(
        self,
        db: Session,
        offer_id: int,
        proposal_id: int,
        runner_id: int,
        proposal_title: str
    ) -> None:
        """
        Notify runner when their offer is accepted.

        Args:
            db: Database session
            offer_id: Accepted offer ID
            proposal_id: Related proposal ID
            runner_id: Runner user ID
            proposal_title: Title of the proposal
        """
        if self._should_send_notification(db, runner_id, NotificationType.OFFER_ACCEPTED):
            self.fcm_service.send_to_user(
                db=db,
                user_id=runner_id,
                notification_type=NotificationType.OFFER_ACCEPTED,
                title="제안이 수락되었습니다!",
                body=f"'{proposal_title}' 제안이 수락되었습니다. 미션을 시작하세요!",
                related_entity_type="offer",
                related_entity_id=offer_id,
                data={"offer_id": offer_id, "proposal_id": proposal_id}
            )

    def notify_offer_rejected(
        self,
        db: Session,
        offer_id: int,
        proposal_id: int,
        runner_id: int,
        proposal_title: str
    ) -> None:
        """
        Notify runner when their offer is rejected.

        Args:
            db: Database session
            offer_id: Rejected offer ID
            proposal_id: Related proposal ID
            runner_id: Runner user ID
            proposal_title: Title of the proposal
        """
        if self._should_send_notification(db, runner_id, NotificationType.OFFER_REJECTED):
            self.fcm_service.send_to_user(
                db=db,
                user_id=runner_id,
                notification_type=NotificationType.OFFER_REJECTED,
                title="제안이 거절되었습니다",
                body=f"'{proposal_title}' 제안이 거절되었습니다.",
                related_entity_type="offer",
                related_entity_id=offer_id,
                data={"offer_id": offer_id, "proposal_id": proposal_id}
            )

    # ========== Mission Events ==========

    def notify_mission_started(
        self,
        db: Session,
        mission_id: int,
        customer_id: int,
        runner_id: int,
        mission_title: str
    ) -> None:
        """
        Notify customer and runner when a mission starts.

        Args:
            db: Database session
            mission_id: Mission ID
            customer_id: Customer user ID
            runner_id: Runner user ID
            mission_title: Title of the mission
        """
        # Notify customer
        if self._should_send_notification(db, customer_id, NotificationType.MISSION_STARTED):
            self.fcm_service.send_to_user(
                db=db,
                user_id=customer_id,
                notification_type=NotificationType.MISSION_STARTED,
                title="미션이 시작되었습니다",
                body=f"'{mission_title}' 미션이 진행 중입니다.",
                related_entity_type="mission",
                related_entity_id=mission_id,
                data={"mission_id": mission_id, "runner_id": runner_id}
            )

        # Notify runner
        if self._should_send_notification(db, runner_id, NotificationType.MISSION_STARTED):
            self.fcm_service.send_to_user(
                db=db,
                user_id=runner_id,
                notification_type=NotificationType.MISSION_STARTED,
                title="미션을 시작하세요",
                body=f"'{mission_title}' 미션이 시작되었습니다.",
                related_entity_type="mission",
                related_entity_id=mission_id,
                data={"mission_id": mission_id, "customer_id": customer_id}
            )

    def notify_mission_completed(
        self,
        db: Session,
        mission_id: int,
        customer_id: int,
        runner_id: int,
        mission_title: str
    ) -> None:
        """
        Notify customer and runner when a mission is completed.

        Args:
            db: Database session
            mission_id: Mission ID
            customer_id: Customer user ID
            runner_id: Runner user ID
            mission_title: Title of the mission
        """
        # Notify customer
        if self._should_send_notification(db, customer_id, NotificationType.MISSION_COMPLETED):
            self.fcm_service.send_to_user(
                db=db,
                user_id=customer_id,
                notification_type=NotificationType.MISSION_COMPLETED,
                title="미션이 완료되었습니다!",
                body=f"'{mission_title}' 미션이 성공적으로 완료되었습니다.",
                related_entity_type="mission",
                related_entity_id=mission_id,
                data={"mission_id": mission_id, "runner_id": runner_id}
            )

        # Notify runner
        if self._should_send_notification(db, runner_id, NotificationType.MISSION_COMPLETED):
            self.fcm_service.send_to_user(
                db=db,
                user_id=runner_id,
                notification_type=NotificationType.MISSION_COMPLETED,
                title="미션 완료!",
                body=f"'{mission_title}' 미션을 완료했습니다. 수고하셨습니다!",
                related_entity_type="mission",
                related_entity_id=mission_id,
                data={"mission_id": mission_id, "customer_id": customer_id}
            )

    # ========== Payment Events ==========

    def notify_payment_completed(
        self,
        db: Session,
        payment_id: int,
        user_id: int,
        amount: int,
        mission_title: str
    ) -> None:
        """
        Notify user when payment is completed.

        Args:
            db: Database session
            payment_id: Payment ID
            user_id: User ID to notify
            amount: Payment amount
            mission_title: Title of related mission
        """
        if self._should_send_notification(db, user_id, NotificationType.PAYMENT_COMPLETED):
            self.fcm_service.send_to_user(
                db=db,
                user_id=user_id,
                notification_type=NotificationType.PAYMENT_COMPLETED,
                title="결제가 완료되었습니다",
                body=f"'{mission_title}' 미션 결제 {amount:,}원이 완료되었습니다.",
                related_entity_type="payment",
                related_entity_id=payment_id,
                data={"payment_id": payment_id, "amount": str(amount)}
            )

    def notify_payment_failed(
        self,
        db: Session,
        payment_id: int,
        user_id: int,
        amount: int,
        mission_title: str,
        reason: Optional[str] = None
    ) -> None:
        """
        Notify user when payment fails.

        Args:
            db: Database session
            payment_id: Payment ID
            user_id: User ID to notify
            amount: Payment amount
            mission_title: Title of related mission
            reason: Optional failure reason
        """
        if self._should_send_notification(db, user_id, NotificationType.PAYMENT_FAILED):
            body = f"'{mission_title}' 미션 결제 {amount:,}원이 실패했습니다."
            if reason:
                body += f" 사유: {reason}"

            self.fcm_service.send_to_user(
                db=db,
                user_id=user_id,
                notification_type=NotificationType.PAYMENT_FAILED,
                title="결제가 실패했습니다",
                body=body,
                related_entity_type="payment",
                related_entity_id=payment_id,
                data={"payment_id": payment_id, "amount": str(amount), "reason": reason or ""}
            )

    # ========== System Events ==========

    def notify_system_announcement(
        self,
        db: Session,
        user_ids: list[int],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send system-wide announcement to specific users.

        Args:
            db: Database session
            user_ids: List of user IDs to notify
            title: Announcement title
            body: Announcement body
            data: Optional additional data
        """
        for user_id in user_ids:
            if self._should_send_notification(db, user_id, NotificationType.SYSTEM_ANNOUNCEMENT):
                self.fcm_service.send_to_user(
                    db=db,
                    user_id=user_id,
                    notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
                    title=title,
                    body=body,
                    data=data
                )

    # ========== Custom Notifications ==========

    def send_custom_notification(
        self,
        db: Session,
        user_id: int,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[int] = None,
        image: Optional[str] = None
    ) -> None:
        """
        Send a custom notification (bypasses preference check).

        Args:
            db: Database session
            user_id: User ID to notify
            title: Notification title
            body: Notification body
            data: Optional data payload
            related_entity_type: Optional related entity type
            related_entity_id: Optional related entity ID
            image: Optional image URL
        """
        self.fcm_service.send_to_user(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.CUSTOM,
            title=title,
            body=body,
            data=data,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            image=image
        )
