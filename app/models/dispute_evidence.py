"""Dispute evidence model."""

from __future__ import annotations

from sqlalchemy import BigInteger, Column, DateTime, Index, String, Text

from app.core.database import Base
from app.core.time import utcnow_naive


class DisputeEvidence(Base):
    """Reason recorded when an accepted offer execution enters dispute."""

    __tablename__ = "dispute_evidences"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proposal_id = Column(BigInteger, nullable=False, index=True)
    offer_id = Column(BigInteger, nullable=False, index=True)
    actor_id = Column(String(36), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    survey_question_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive)

    __table_args__ = (
        Index("idx_dispute_evidences_survey_question_id", "survey_question_id"),
    )


__all__ = ["DisputeEvidence"]
