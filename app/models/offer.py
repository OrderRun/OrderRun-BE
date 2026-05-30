"""Offer model representing runner offers for proposals."""
from sqlalchemy import Column, BigInteger, Integer, String, Enum, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class OfferStatus(str, enum.Enum):
    """Offer status enumeration."""
    WAITING = "WAITING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class Offer(Base):
    """Offer model representing runner offers for proposals."""

    __tablename__ = "offers"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    proposal_id = Column(Integer, nullable=False, index=True)
    runner_id = Column(String(36), nullable=False, index=True)
    estimated_time = Column(Integer, nullable=False)
    message = Column(String(500), nullable=True)
    status = Column(Enum(OfferStatus), nullable=False, default=OfferStatus.WAITING, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Unique constraint: one offer per runner per proposal
    __table_args__ = (
        UniqueConstraint('proposal_id', 'runner_id', name='uq_proposal_runner'),
    )

    def __repr__(self):
        return f"<Offer(id={self.id}, proposal_id={self.proposal_id}, runner_id={self.runner_id}, status={self.status})>"

    def can_modify(self) -> bool:
        """Check if the offer can be modified."""
        return self.status == OfferStatus.WAITING

    def accept(self):
        """Accept the offer."""
        if not self.can_modify():
            raise ValueError("Cannot accept offer that is not in WAITING status")
        self.status = OfferStatus.ACCEPTED

    def reject(self):
        """Reject the offer."""
        if not self.can_modify():
            raise ValueError("Cannot reject offer that is not in WAITING status")
        self.status = OfferStatus.REJECTED
