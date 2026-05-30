"""Offer model representing runner applications for proposals."""

from __future__ import annotations

import enum

from sqlalchemy import BigInteger, Column, DateTime, Enum, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class OfferStatus(str, enum.Enum):
    """Offer status enumeration."""

    WAITING = "WAITING"
    ACCEPTED = "ACCEPTED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class Offer(Base):
    """Runner application submitted against a proposal."""

    __tablename__ = "offers"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    proposal_id = Column(BigInteger().with_variant(Integer, "sqlite"), nullable=False, index=True)
    runner_id = Column(String(36), nullable=False, index=True)
    status = Column(Enum(OfferStatus), nullable=False, default=OfferStatus.WAITING, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

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

    def reject(self) -> None:
        if self.status != OfferStatus.WAITING:
            raise ValueError("Cannot reject offer that is not in WAITING status")
        self.status = OfferStatus.REJECTED

    def cancel(self) -> None:
        if not self.can_cancel():
            raise ValueError("Cannot cancel offer that is not in WAITING status")
        self.status = OfferStatus.CANCELLED
