"""Notification Event Dispatcher — routes business events to FCM push notifications."""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.notification import NotificationType
from app.models.user import User
from app.services.fcm_service import FCMService


logger = logging.getLogger(__name__)


class NotificationDispatcher:
    def __init__(self, fcm_service: FCMService):
        self.fcm_service = fcm_service

    def _should_send_notification(self, db: Session, user_id: str) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        return user is not None and user.alarm_enabled

    def notify_proposal_created(self, db: Session, proposal_id: int, creator_id: str, proposal_title: str) -> None:
        logger.info(f"Proposal {proposal_id} created by user {creator_id}: {proposal_title}")

    def notify_proposal_matched(
        self, db: Session, proposal_id: int, customer_id: str, runner_id: str, proposal_title: str
    ) -> None:
        if self._should_send_notification(db, customer_id):
            self.fcm_service.send_to_user(
                db=db, user_id=customer_id, notification_type=NotificationType.PROPOSAL_MATCHED,
                title="의뢰가 매칭되었습니다!", body=f"'{proposal_title}' 의뢰에 러너가 배정되었습니다.",
                related_entity_type="proposal", related_entity_id=proposal_id,
                data={"proposal_id": proposal_id, "runner_id": runner_id},
            )
        if self._should_send_notification(db, runner_id):
            self.fcm_service.send_to_user(
                db=db, user_id=runner_id, notification_type=NotificationType.PROPOSAL_MATCHED,
                title="새로운 미션이 배정되었습니다!", body=f"'{proposal_title}' 미션을 시작하세요.",
                related_entity_type="proposal", related_entity_id=proposal_id,
                data={"proposal_id": proposal_id, "customer_id": customer_id},
            )

    def notify_proposal_cancelled(
        self, db: Session, proposal_id: int, affected_user_ids: list[str], proposal_title: str, reason: Optional[str] = None
    ) -> None:
        body = f"'{proposal_title}' 의뢰가 취소되었습니다."
        if reason:
            body += f" 사유: {reason}"
        for user_id in affected_user_ids:
            if self._should_send_notification(db, user_id):
                self.fcm_service.send_to_user(
                    db=db, user_id=user_id, notification_type=NotificationType.PROPOSAL_CANCELLED,
                    title="의뢰가 취소되었습니다", body=body,
                    related_entity_type="proposal", related_entity_id=proposal_id,
                    data={"proposal_id": proposal_id, "reason": reason or ""},
                )

    def notify_offer_received(
        self, db: Session, offer_id: int, proposal_id: int, customer_id: str, runner_id: str,
        proposal_title: str, offer_amount: int
    ) -> None:
        if self._should_send_notification(db, customer_id):
            self.fcm_service.send_to_user(
                db=db, user_id=customer_id, notification_type=NotificationType.OFFER_NEW,
                title="새로운 제안이 도착했습니다!", body=f"'{proposal_title}' 의뢰에 {offer_amount:,}원의 제안이 왔습니다.",
                related_entity_type="offer", related_entity_id=offer_id,
                data={"offer_id": offer_id, "proposal_id": proposal_id, "runner_id": runner_id, "amount": str(offer_amount)},
            )

    def notify_offer_accepted(
        self, db: Session, offer_id: int, proposal_id: int, runner_id: str, proposal_title: str
    ) -> None:
        if self._should_send_notification(db, runner_id):
            self.fcm_service.send_to_user(
                db=db, user_id=runner_id, notification_type=NotificationType.OFFER_ACCEPTED,
                title="제안이 수락되었습니다!", body=f"'{proposal_title}' 제안이 수락되었습니다. 미션을 시작하세요!",
                related_entity_type="offer", related_entity_id=offer_id,
                data={"offer_id": offer_id, "proposal_id": proposal_id},
            )

    def notify_offer_rejected(
        self, db: Session, offer_id: int, proposal_id: int, runner_id: str, proposal_title: str
    ) -> None:
        if self._should_send_notification(db, runner_id):
            self.fcm_service.send_to_user(
                db=db, user_id=runner_id, notification_type=NotificationType.OFFER_REJECTED,
                title="제안이 거절되었습니다", body=f"'{proposal_title}' 제안이 거절되었습니다.",
                related_entity_type="offer", related_entity_id=offer_id,
                data={"offer_id": offer_id, "proposal_id": proposal_id},
            )

    def notify_execution_started(
        self, db: Session, offer_id: int, proposal_id: int, customer_id: str, runner_id: str, proposal_title: str
    ) -> None:
        if self._should_send_notification(db, customer_id):
            self.fcm_service.send_to_user(
                db=db, user_id=customer_id, notification_type=NotificationType.EXECUTION_STARTED,
                title="수행이 시작되었습니다", body=f"'{proposal_title}' 요청이 진행 중입니다.",
                related_entity_type="offer", related_entity_id=offer_id,
                data={"offer_id": offer_id, "proposal_id": proposal_id, "runner_id": runner_id},
            )
        if self._should_send_notification(db, runner_id):
            self.fcm_service.send_to_user(
                db=db, user_id=runner_id, notification_type=NotificationType.EXECUTION_STARTED,
                title="수행을 시작하세요", body=f"'{proposal_title}' 요청이 시작되었습니다.",
                related_entity_type="offer", related_entity_id=offer_id,
                data={"offer_id": offer_id, "proposal_id": proposal_id, "customer_id": customer_id},
            )

    def notify_execution_completed(
        self, db: Session, offer_id: int, proposal_id: int, customer_id: str, runner_id: str, proposal_title: str
    ) -> None:
        if self._should_send_notification(db, customer_id):
            self.fcm_service.send_to_user(
                db=db, user_id=customer_id, notification_type=NotificationType.EXECUTION_COMPLETED,
                title="수행이 완료되었습니다!", body=f"'{proposal_title}' 요청이 성공적으로 완료되었습니다.",
                related_entity_type="offer", related_entity_id=offer_id,
                data={"offer_id": offer_id, "proposal_id": proposal_id, "runner_id": runner_id},
            )
        if self._should_send_notification(db, runner_id):
            self.fcm_service.send_to_user(
                db=db, user_id=runner_id, notification_type=NotificationType.EXECUTION_COMPLETED,
                title="수행 완료!", body=f"'{proposal_title}' 요청을 완료했습니다. 수고하셨습니다!",
                related_entity_type="offer", related_entity_id=offer_id,
                data={"offer_id": offer_id, "proposal_id": proposal_id, "customer_id": customer_id},
            )

    def notify_payment_completed(
        self, db: Session, payment_id: int, user_id: str, amount: int, proposal_title: str
    ) -> None:
        if self._should_send_notification(db, user_id):
            self.fcm_service.send_to_user(
                db=db, user_id=user_id, notification_type=NotificationType.PAYMENT_COMPLETED,
                title="결제가 완료되었습니다", body=f"'{proposal_title}' 요청 결제 {amount:,}원이 완료되었습니다.",
                related_entity_type="payment", related_entity_id=payment_id,
                data={"payment_id": payment_id, "amount": str(amount)},
            )

    def notify_payment_failed(
        self, db: Session, payment_id: int, user_id: str, amount: int, proposal_title: str, reason: Optional[str] = None
    ) -> None:
        if self._should_send_notification(db, user_id):
            body = f"'{proposal_title}' 요청 결제 {amount:,}원이 실패했습니다."
            if reason:
                body += f" 사유: {reason}"
            self.fcm_service.send_to_user(
                db=db, user_id=user_id, notification_type=NotificationType.PAYMENT_FAILED,
                title="결제가 실패했습니다", body=body,
                related_entity_type="payment", related_entity_id=payment_id,
                data={"payment_id": payment_id, "amount": str(amount), "reason": reason or ""},
            )

    def notify_system_announcement(
        self, db: Session, user_ids: list[str], title: str, body: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        for user_id in user_ids:
            if self._should_send_notification(db, user_id):
                self.fcm_service.send_to_user(
                    db=db, user_id=user_id, notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
                    title=title, body=body, data=data,
                )

    def send_custom_notification(
        self, db: Session, user_id: str, title: str, body: str,
        data: Optional[Dict[str, Any]] = None, related_entity_type: Optional[str] = None,
        related_entity_id: Optional[int] = None, image: Optional[str] = None,
    ) -> None:
        self.fcm_service.send_to_user(
            db=db, user_id=user_id, notification_type=NotificationType.CUSTOM,
            title=title, body=body, data=data,
            related_entity_type=related_entity_type, related_entity_id=related_entity_id, image=image,
        )
