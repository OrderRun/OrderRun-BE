"""Notification event listener — domain events → PENDING Notification records."""
from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from app.events.base import EventBus
from app.events.offer_events import OfferCreatedEvent, OfferAcceptedEvent
from app.events.execution_events import (
    DisputeRaisedByOrdererEvent,
    DisputeRaisedByRunnerEvent,
    MeetingConfirmedByOrdererEvent,
    MeetingConfirmedByRunnerEvent,
)
from app.models.notification import Notification, NotificationStatus, NotificationType
from app.models.user import User

logger = logging.getLogger(__name__)


def _alarm_enabled(db: Session, user_id: str) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    return user is not None and user.alarm_enabled


def _pending(
    user_id: str,
    notification_type: NotificationType,
    title: str,
    body: str,
    related_entity_type: str,
    related_entity_id: int,
    data: dict | None = None,
) -> Notification:
    import json
    return Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        body=body,
        data=json.dumps(data) if data else None,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        status=NotificationStatus.PENDING,
    )


def _add_execution_completed_notifications(
    event: MeetingConfirmedByRunnerEvent | MeetingConfirmedByOrdererEvent,
    db: Session,
) -> None:
    for user_id in (event.orderer_id, event.runner_id):
        if _alarm_enabled(db, user_id):
            db.add(_pending(
                user_id=user_id,
                notification_type=NotificationType.EXECUTION_COMPLETED,
                title="완료! 수고하셨어요 🎊",
                body="양측 만남이 모두 확인됐어요. 성공적으로 완료됐습니다!",
                related_entity_type="offer",
                related_entity_id=event.offer_id,
                data={"offer_id": event.offer_id, "proposal_id": event.proposal_id},
            ))


def on_offer_created(event: OfferCreatedEvent, db: Session) -> None:
    if _alarm_enabled(db, event.orderer_id):
        db.add(_pending(
            user_id=event.orderer_id,
            notification_type=NotificationType.OFFER_NEW,
            title="누군가 지원했어요! 👀",
            body="회원님의 요청에 새로운 지원자가 생겼어요. 확인해보세요!",
            related_entity_type="offer",
            related_entity_id=event.offer_id,
            data={"offer_id": event.offer_id, "proposal_id": event.proposal_id},
        ))

    if _alarm_enabled(db, event.runner_id):
        db.add(_pending(
            user_id=event.runner_id,
            notification_type=NotificationType.OFFER_SUBMITTED,
            title="지원 완료! ✅",
            body="지원이 정상적으로 접수됐어요. 요청자의 선택을 기다려주세요.",
            related_entity_type="offer",
            related_entity_id=event.offer_id,
            data={"offer_id": event.offer_id, "proposal_id": event.proposal_id},
        ))


def on_offer_accepted(event: OfferAcceptedEvent, db: Session) -> None:
    if _alarm_enabled(db, event.accepted_runner_id):
        db.add(_pending(
            user_id=event.accepted_runner_id,
            notification_type=NotificationType.OFFER_ACCEPTED,
            title="선택받으셨어요! 🙌",
            body="요청자가 회원님을 선택했어요.",
            related_entity_type="offer",
            related_entity_id=event.offer_id,
            data={"offer_id": event.offer_id, "proposal_id": event.proposal_id},
        ))

    for runner_id in event.rejected_runner_ids:
        if _alarm_enabled(db, runner_id):
            db.add(_pending(
                user_id=runner_id,
                notification_type=NotificationType.OFFER_REJECTED,
                title="이번엔 아쉽게 됐어요 😢",
                body="이번엔 선택받지 못했지만 다음 기회가 분명 있을 거예요.",
                related_entity_type="offer",
                related_entity_id=event.offer_id,
                data={"offer_id": event.offer_id, "proposal_id": event.proposal_id},
            ))


def on_meeting_confirmed_by_runner(event: MeetingConfirmedByRunnerEvent, db: Session) -> None:
    if event.all_completed:
        _add_execution_completed_notifications(event, db)
        return

    if _alarm_enabled(db, event.orderer_id):
        db.add(_pending(
            user_id=event.orderer_id,
            notification_type=NotificationType.MEETING_CONFIRMED,
            title="지원자가 만남을 확인했어요! 🤝",
            body="지원자가 만남을 확인했어요. 회원님도 확인해주시면 정산이 바로 진행돼요.",
            related_entity_type="offer",
            related_entity_id=event.offer_id,
            data={"offer_id": event.offer_id, "proposal_id": event.proposal_id},
        ))


def on_meeting_confirmed_by_orderer(event: MeetingConfirmedByOrdererEvent, db: Session) -> None:
    if event.all_completed:
        _add_execution_completed_notifications(event, db)
        return

    if _alarm_enabled(db, event.runner_id):
        db.add(_pending(
            user_id=event.runner_id,
            notification_type=NotificationType.MEETING_CONFIRMED,
            title="요청자가 만남을 확인했어요! 🤝",
            body="요청자가 만남을 확인했어요. 회원님도 앱에서 만남을 확인해주시면 정산이 진행돼요!",
            related_entity_type="offer",
            related_entity_id=event.offer_id,
            data={"offer_id": event.offer_id, "proposal_id": event.proposal_id},
        ))


def on_dispute_raised_by_orderer(event: DisputeRaisedByOrdererEvent, db: Session) -> None:
    if _alarm_enabled(db, event.runner_id):
        db.add(_pending(
            user_id=event.runner_id,
            notification_type=NotificationType.DISPUTE_RAISED,
            title="분쟁이 접수되었어요",
            body="요청자가 분쟁을 접수했어요. 앱에서 내용을 확인해주세요.",
            related_entity_type="offer",
            related_entity_id=event.offer_id,
            data={"offer_id": event.offer_id, "proposal_id": event.proposal_id},
        ))


def on_dispute_raised_by_runner(event: DisputeRaisedByRunnerEvent, db: Session) -> None:
    if _alarm_enabled(db, event.orderer_id):
        db.add(_pending(
            user_id=event.orderer_id,
            notification_type=NotificationType.DISPUTE_RAISED,
            title="분쟁이 접수되었어요",
            body="지원자가 분쟁을 접수했어요. 앱에서 내용을 확인해주세요.",
            related_entity_type="offer",
            related_entity_id=event.offer_id,
            data={"offer_id": event.offer_id, "proposal_id": event.proposal_id},
        ))


def register_all() -> None:
    EventBus.register(OfferCreatedEvent, on_offer_created)
    EventBus.register(OfferAcceptedEvent, on_offer_accepted)
    EventBus.register(MeetingConfirmedByRunnerEvent, on_meeting_confirmed_by_runner)
    EventBus.register(MeetingConfirmedByOrdererEvent, on_meeting_confirmed_by_orderer)
    EventBus.register(DisputeRaisedByOrdererEvent, on_dispute_raised_by_orderer)
    EventBus.register(DisputeRaisedByRunnerEvent, on_dispute_raised_by_runner)
