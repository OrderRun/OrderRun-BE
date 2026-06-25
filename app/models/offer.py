"""Offer model representing runner applications for proposals."""

from __future__ import annotations

import enum

from sqlalchemy import BigInteger, Column, DateTime, Enum, String, UniqueConstraint

from app.core.time import utcnow_naive
from app.core.database import Base


class OfferStatus(str, enum.Enum):
    """Offer status enumeration."""

    WAITING = "WAITING"
    ACCEPTED = "ACCEPTED"
    RUNNER_COMPLETED = "RUNNER_COMPLETED"
    ALL_COMPLETED = "ALL_COMPLETED"
    DISPUTED = "DISPUTED"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class Offer(Base):
    """Runner application submitted against a proposal."""

    __tablename__ = "offers"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proposal_id = Column(BigInteger, nullable=False, index=True)
    runner_id = Column(String(36), nullable=False, index=True)
    status = Column(Enum(OfferStatus), nullable=False, default=OfferStatus.WAITING, index=True)
    open_chat_url = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    runner_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    orderer_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    disputed_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive, onupdate=utcnow_naive)

    __table_args__ = (
        UniqueConstraint("proposal_id", "runner_id", name="uk_proposal_runner"),
    )

    def __repr__(self):
        return f"<Offer(id={self.id}, proposal_id={self.proposal_id}, runner_id={self.runner_id}, status={self.status})>"

    def can_accept(self) -> bool:
        return self.status == OfferStatus.WAITING

    def can_cancel(self) -> bool:
        return self.status == OfferStatus.WAITING

    def accept(self) -> None:
        if not self.can_accept():
            raise ValueError("Cannot accept offer that is not in WAITING status")
        self.status = OfferStatus.ACCEPTED
        self.accepted_at = utcnow_naive()

    def can_confirm_runner_completion(self) -> bool:
        return self.status == OfferStatus.ACCEPTED

    def confirm_runner_completion(self) -> None:
        if not self.can_confirm_runner_completion():
            raise ValueError("Cannot confirm runner completion for offer not in ACCEPTED status")
        self.status = OfferStatus.RUNNER_COMPLETED
        self.runner_confirmed_at = utcnow_naive()

    def can_confirm_orderer_completion(self) -> bool:
        return self.status in {OfferStatus.ACCEPTED, OfferStatus.RUNNER_COMPLETED}

    def confirm_orderer_completion(self) -> None:
        if not self.can_confirm_orderer_completion():
            raise ValueError("Cannot confirm orderer completion for offer not in active execution status")
        self.orderer_confirmed_at = utcnow_naive()

    def mark_all_completed(self) -> None:
        if self.status not in {OfferStatus.RUNNER_COMPLETED, OfferStatus.ACCEPTED}:
            raise ValueError("Cannot mark all completed for offer at this stage")
        self.status = OfferStatus.ALL_COMPLETED

    def can_raise_dispute(self) -> bool:
        return self.status in {
            OfferStatus.ACCEPTED,
            OfferStatus.RUNNER_COMPLETED,
        }

    def raise_dispute(self) -> None:
        if not self.can_raise_dispute():
            raise ValueError("Cannot raise dispute for offer at this stage")
        self.status = OfferStatus.DISPUTED
        self.disputed_at = utcnow_naive()

    def can_resolve(self) -> bool:
        return self.status == OfferStatus.DISPUTED

    def resolve(self) -> None:
        if not self.can_resolve():
            raise ValueError("Cannot resolve offer not in DISPUTED status")
        self.status = OfferStatus.RESOLVED
        self.resolved_at = utcnow_naive()

    def reject(self) -> None:
        if self.status != OfferStatus.WAITING:
            raise ValueError("Cannot reject offer that is not in WAITING status")
        self.status = OfferStatus.REJECTED

    def cancel(self) -> None:
        if not self.can_cancel():
            raise ValueError("Cannot cancel offer that is not in WAITING status")
        self.status = OfferStatus.CANCELLED
