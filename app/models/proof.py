"""Proof model for delivery and dispute evidence."""

from __future__ import annotations

import enum

from sqlalchemy import BigInteger, Column, DateTime, Enum, String, Text

from app.core.database import Base
from app.core.time import utcnow_naive


class ProofType(str, enum.Enum):
    """Proof type enumeration."""

    DELIVERY = "DELIVERY"
    DISPUTE = "DISPUTE"


class Proof(Base):
    """Evidence or reason recorded during accepted offer execution."""

    __tablename__ = "proofs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proposal_id = Column(BigInteger, nullable=False, index=True)
    offer_id = Column(BigInteger, nullable=False, index=True)
    actor_id = Column(String(36), nullable=False, index=True)
    proof_type = Column(Enum(ProofType), nullable=False, index=True)
    image_url = Column(String(500), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive)
