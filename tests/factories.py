"""Shared test data factories."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.notification import Notification, NotificationStatus, NotificationType
from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.user import User


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TestDataFactory:
    def __init__(self, db: Session):
        self.db = db

    def headers_for(self, user: User) -> dict:
        return {"Authorization": f"Bearer {create_access_token({'sub': user.id})}"}

    def user(self, phone: str = "01099990000", name: str = "Test User") -> User:
        user = User(name=name, phone=phone, alarm_enabled=False)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def proposal(
        self,
        orderer_id: str,
        status: ProposalStatus = ProposalStatus.POSTED,
        title: str = "요청",
    ) -> Proposal:
        deadline = datetime.now(timezone.utc) + timedelta(days=1)
        proposal = Proposal(
            orderer_id=orderer_id,
            title=title,
            content="요청 내용",
            deadline=deadline,
            errand_fee=5000,
            status=status,
            meeting_at=deadline,
            item_price=0,
            deposit=0,
        )
        # Set timestamps based on status
        if status in {ProposalStatus.ORDER_COMPLETED, ProposalStatus.ALL_COMPLETED}:
            proposal.orderer_confirmed_at = utcnow_naive()
        if status == ProposalStatus.MATCHED:
            proposal.matched_at = utcnow_naive()
        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def offer(
        self,
        proposal_id: int,
        runner_id: str,
        status: OfferStatus = OfferStatus.WAITING,
    ) -> Offer:
        offer = Offer(proposal_id=proposal_id, runner_id=runner_id, status=status)
        self.db.add(offer)
        self.db.commit()
        self.db.refresh(offer)
        return offer

    def execution(
        self,
        orderer: User,
        runner: User,
        proposal_status: ProposalStatus = ProposalStatus.MATCHED,
        offer_status: OfferStatus = OfferStatus.ACCEPTED,
    ) -> tuple[Proposal, Offer]:
        proposal = self.proposal(orderer.id, proposal_status)
        offer = self.offer(proposal.id, runner.id, offer_status)
        return proposal, offer

    def notification(self, user_id: str, **overrides) -> Notification:
        values = {
            "user_id": user_id,
            "notification_type": NotificationType.CUSTOM,
            "title": "테스트 알림",
            "body": "테스트 알림 본문입니다.",
            "data": '{"proposalId":1}',
            "related_entity_type": "proposal",
            "related_entity_id": 1,
            "status": NotificationStatus.SENT,
            "fcm_message_id": "projects/orderrun/messages/1",
            "sent_at": utcnow_naive(),
        }
        values.update(overrides)
        notification = Notification(**values)
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification
