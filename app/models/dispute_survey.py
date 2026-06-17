"""Dispute survey question persistence model."""

from __future__ import annotations

import enum

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Index, Integer, String, UniqueConstraint

from app.core.database import Base
from app.core.time import utcnow_naive


class DisputeSurveyTargetType(str, enum.Enum):
    """Dispute survey question target type."""

    ORDER = "ORDER"
    RUNNER = "RUNNER"


class DisputeSurveyQuestion(Base):
    """Question master data shown before dispute submission."""

    __tablename__ = "dispute_survey_questions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    target_type = Column(Enum(DisputeSurveyTargetType), nullable=False)
    question_text = Column(String(500), nullable=False)
    display_order = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive, onupdate=utcnow_naive)

    __table_args__ = (
        UniqueConstraint("target_type", "display_order", name="uk_dispute_survey_questions_target_order"),
        Index("idx_dispute_survey_questions_lookup", "target_type", "is_active", "display_order", "id"),
    )


__all__ = ["DisputeSurveyQuestion", "DisputeSurveyTargetType"]
