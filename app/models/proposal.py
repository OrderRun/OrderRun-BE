"""Proposal persistence model for errand requests."""

from __future__ import annotations

import enum

from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class ProposalStatus(str, enum.Enum):
    """Proposal lifecycle status matching the Java API contract."""

    HOLDING = "HOLDING"
    POSTED = "POSTED"
    OFFERED = "OFFERED"
    MATCHED = "MATCHED"
    CANCELLED = "CANCELLED"


class Proposal(Base):
    """Errand recruitment post created by an orderer."""

    __tablename__ = "proposals"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
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

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (Index("idx_proposals_orderer_id", "orderer_id"),)

    def can_receive_offers(self) -> bool:
        return self.status in {ProposalStatus.POSTED, ProposalStatus.OFFERED}

    def mark_as_offered(self) -> None:
        if self.status == ProposalStatus.POSTED:
            self.status = ProposalStatus.OFFERED
