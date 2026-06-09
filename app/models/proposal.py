"""Proposal persistence model for errand requests."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Integer, String

from app.core.database import Base
from app.core.errors import AppError, api_error
from app.core.time import utcnow_naive


class ProposalStatus(str, enum.Enum):
    """Proposal lifecycle status matching the Java API contract."""

    HOLDING = "HOLDING"
    POSTED = "POSTED"
    OFFERED = "OFFERED"
    MATCHED = "MATCHED"
    COMPLETED = "COMPLETED"
    ALL_COMPLETED = "ALL_COMPLETED"
    SETTLED = "SETTLED"
    DISPUTED = "DISPUTED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class Proposal(Base):
    """Errand recruitment post created by an orderer."""

    __tablename__ = "proposals"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    orderer_id = Column(String(36), nullable=False, index=True)
    title = Column(String(50), nullable=False)
    content = Column(String(500), nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=False)
    errand_fee = Column(Integer, nullable=False)
    status = Column(Enum(ProposalStatus), nullable=False, default=ProposalStatus.HOLDING, index=True)

    # Kept for migration compatibility. These fields are not exposed by the current Java Proposal API.
    meeting_at = Column(DateTime(timezone=True), nullable=False)
    item_price = Column(Integer, nullable=False, default=0, server_default="0")
    deposit = Column(Integer, nullable=False, default=0, server_default="0")

    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive)
    matched_at = Column(DateTime(timezone=True), nullable=True)
    delivery_reported_at = Column(DateTime(timezone=True), nullable=True)
    received_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    settled_at = Column(DateTime(timezone=True), nullable=True)
    disputed_at = Column(DateTime(timezone=True), nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive, onupdate=utcnow_naive)

    __table_args__ = (Index("idx_proposals_orderer_id", "orderer_id"),)

    def can_receive_offers(self) -> bool:
        return self.status in {ProposalStatus.POSTED, ProposalStatus.OFFERED}

    def mark_as_offered(self) -> None:
        if self.status == ProposalStatus.POSTED:
            self.status = ProposalStatus.OFFERED

    def can_report_delivery(self) -> bool:
        return self.status == ProposalStatus.MATCHED

    def report_delivery(self) -> None:
        if not self.can_report_delivery():
            raise ValueError("Cannot report delivery for proposal not in MATCHED status")
        self.delivery_reported_at = utcnow_naive()

    def can_confirm_receipt(self) -> bool:
        return self.status == ProposalStatus.MATCHED

    def confirm_receipt(self) -> None:
        if not self.can_confirm_receipt():
            raise ValueError("Cannot confirm receipt for proposal not in MATCHED status")
        self.status = ProposalStatus.COMPLETED
        self.received_confirmed_at = utcnow_naive()

    def mark_all_completed(self) -> None:
        if self.status not in {ProposalStatus.COMPLETED, ProposalStatus.MATCHED}:
            raise ValueError("Cannot mark all completed for proposal at this stage")
        self.status = ProposalStatus.ALL_COMPLETED

    def can_settle(self) -> bool:
        return self.status == ProposalStatus.ALL_COMPLETED

    def settle(self) -> None:
        if not self.can_settle():
            raise ValueError("Cannot settle proposal not in ALL_COMPLETED status")
        self.status = ProposalStatus.SETTLED
        self.settled_at = utcnow_naive()

    def can_raise_dispute(self) -> bool:
        return self.status in {
            ProposalStatus.MATCHED,
            ProposalStatus.COMPLETED,
            ProposalStatus.ALL_COMPLETED,
        }

    def raise_dispute(self) -> None:
        if not self.can_raise_dispute():
            raise ValueError("Cannot raise dispute for proposal at this stage")
        self.status = ProposalStatus.DISPUTED
        self.disputed_at = utcnow_naive()

    def can_refund(self) -> bool:
        return self.status == ProposalStatus.DISPUTED

    def refund(self) -> None:
        if not self.can_refund():
            raise ValueError("Cannot refund proposal not in DISPUTED status")
        self.status = ProposalStatus.REFUNDED
        self.refunded_at = utcnow_naive()

    @classmethod
    def create_proposal(
        cls,
        orderer_id: str,
        title: str,
        content: str,
        deadline: datetime,
        errand_fee: int,
    ) -> "Proposal":
        validated_deadline = cls._validate_deadline(deadline)
        cls._validate_errand_fee(errand_fee)
        return cls(
            orderer_id=orderer_id,
            title=title,
            content=content,
            deadline=validated_deadline,
            errand_fee=errand_fee,
            status=ProposalStatus.HOLDING,
            meeting_at=validated_deadline,
            item_price=0,
            deposit=0,
        )

    def update_proposal(
        self,
        title: str,
        content: str,
        deadline: datetime,
        errand_fee: int,
    ) -> None:
        validated_deadline = self._validate_deadline(deadline)
        self._validate_errand_fee(errand_fee)
        self.title = title
        self.content = content
        self.deadline = validated_deadline
        self.errand_fee = errand_fee
        self.meeting_at = validated_deadline
        self.status = ProposalStatus.HOLDING

    @staticmethod
    def _validate_deadline(deadline: datetime) -> datetime:
        deadline_utc = deadline.astimezone(timezone.utc)
        if deadline_utc <= datetime.now(timezone.utc):
            raise api_error(AppError.PROPOSAL_DEADLINE_INVALID)
        return deadline_utc

    @staticmethod
    def _validate_errand_fee(errand_fee: int) -> None:
        if errand_fee < 1000:
            raise api_error(AppError.PROPOSAL_ERRAND_FEE_INVALID, "errandFee must be greater than or equal to 1000")
