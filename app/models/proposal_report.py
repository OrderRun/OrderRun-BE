"""Proposal report persistence models."""

from __future__ import annotations

import enum

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Index, Integer, String, UniqueConstraint

from app.core.database import Base
from app.core.time import utcnow_naive


class ProposalReportStatus(str, enum.Enum):
    """Moderation state of a submitted Proposal report."""

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class ProposalReportReasonQuestion(Base):
    """Active report-reason choices displayed to users."""

    __tablename__ = "proposal_report_reason_questions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    question_text = Column(String(500), nullable=False)
    display_order = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive, onupdate=utcnow_naive)

    __table_args__ = (
        UniqueConstraint("display_order", name="uk_proposal_report_reason_questions_display_order"),
        Index("idx_proposal_report_reason_questions_lookup", "is_active", "display_order", "id"),
    )


class ProposalReport(Base):
    """A user's report against a public Proposal."""

    __tablename__ = "proposal_reports"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proposal_id = Column(BigInteger, nullable=False)
    reporter_id = Column(String(36), nullable=False)
    reason_question_id = Column(BigInteger, nullable=False)
    detail_reason = Column(String(500), nullable=True)
    status = Column(Enum(ProposalReportStatus), nullable=False, default=ProposalReportStatus.PENDING)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive, onupdate=utcnow_naive)

    __table_args__ = (
        UniqueConstraint("proposal_id", "reporter_id", name="uk_proposal_reports_proposal_reporter"),
        Index("idx_proposal_reports_proposal_status", "proposal_id", "status", "id"),
        Index("idx_proposal_reports_reporter_id", "reporter_id"),
        Index("idx_proposal_reports_status_created", "status", "created_at", "id"),
    )


__all__ = ["ProposalReport", "ProposalReportReasonQuestion", "ProposalReportStatus"]
