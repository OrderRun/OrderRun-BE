"""Proposal report commands, moderation, and reason queries."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError, api_error
from app.core.time import utcnow_naive
from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.proposal_report import ProposalReport, ProposalReportReasonQuestion, ProposalReportStatus
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.proposal_report import ProposalReportCreateRequest, ProposalReportReasonQuestionResponse, ProposalReportResponse


REPORTABLE_PROPOSAL_STATUSES = (ProposalStatus.POSTED, ProposalStatus.OFFERED)


class ProposalReportService:
    @staticmethod
    def list_reason_questions(db: Session) -> list[ProposalReportReasonQuestionResponse]:
        questions = (
            db.query(ProposalReportReasonQuestion)
            .filter(ProposalReportReasonQuestion.is_active.is_(True))
            .order_by(ProposalReportReasonQuestion.display_order.asc(), ProposalReportReasonQuestion.id.asc())
            .all()
        )
        return [ProposalReportReasonQuestionResponse.model_validate(question) for question in questions]

    @staticmethod
    def _get_proposal(db: Session, proposal_id: int) -> Proposal:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if proposal is None:
            raise api_error(AppError.PROPOSAL_NOT_FOUND, f"id: {proposal_id}")
        return proposal

    @staticmethod
    def _get_active_reason_question(db: Session, question_id: int) -> ProposalReportReasonQuestion:
        question = (
            db.query(ProposalReportReasonQuestion)
            .filter(
                ProposalReportReasonQuestion.id == question_id,
                ProposalReportReasonQuestion.is_active.is_(True),
            )
            .one_or_none()
        )
        if question is None:
            raise api_error(AppError.VALIDATION_ERROR, "reasonQuestionId")
        return question

    @staticmethod
    def _to_response(report: ProposalReport, question_text: str) -> ProposalReportResponse:
        return ProposalReportResponse(
            id=report.id,
            proposal_id=report.proposal_id,
            reporter_id=report.reporter_id,
            reason_question_id=report.reason_question_id,
            reason_question_text=question_text,
            detail_reason=report.detail_reason,
            status=report.status,
            created_at=report.created_at,
            reviewed_at=report.reviewed_at,
        )

    @staticmethod
    def create(db: Session, proposal_id: int, reporter_id: str, request: ProposalReportCreateRequest) -> ProposalReportResponse:
        proposal = ProposalReportService._get_proposal(db, proposal_id)
        if proposal.orderer_id == reporter_id:
            raise api_error(AppError.PROPOSAL_SELF_REPORT_NOT_ALLOWED)
        if proposal.status not in REPORTABLE_PROPOSAL_STATUSES:
            raise api_error(AppError.PROPOSAL_NOT_REPORTABLE, f"status: {proposal.status.value}")
        question = ProposalReportService._get_active_reason_question(db, request.reason_question_id)
        report = ProposalReport(
            proposal_id=proposal.id,
            reporter_id=reporter_id,
            reason_question_id=question.id,
            detail_reason=request.detail_reason,
            status=ProposalReportStatus.PENDING,
        )
        db.add(report)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise api_error(AppError.DUPLICATE_PROPOSAL_REPORT) from None
        db.refresh(report)
        return ProposalReportService._to_response(report, question.question_text)

    @staticmethod
    def list_reports(
        db: Session, report_status: ProposalReportStatus | None, page: int, size: int
    ) -> PageResponse[ProposalReportResponse]:
        query = db.query(ProposalReport, ProposalReportReasonQuestion.question_text).join(
            ProposalReportReasonQuestion,
            ProposalReport.reason_question_id == ProposalReportReasonQuestion.id,
        )
        if report_status is not None:
            query = query.filter(ProposalReport.status == report_status)
        total = query.count()
        rows = (
            query.order_by(ProposalReport.created_at.asc(), ProposalReport.id.asc())
            .offset(page * size)
            .limit(size)
            .all()
        )
        return PageResponse.of(
            content=[ProposalReportService._to_response(report, question_text) for report, question_text in rows],
            page_number=page,
            page_size=size,
            total_elements=total,
        )

    @staticmethod
    def _get_report(db: Session, report_id: int) -> ProposalReport:
        report = db.query(ProposalReport).filter(ProposalReport.id == report_id).first()
        if report is None:
            raise api_error(AppError.PROPOSAL_REPORT_NOT_FOUND, f"id: {report_id}")
        return report

    @staticmethod
    def _ensure_pending(report: ProposalReport) -> None:
        if report.status != ProposalReportStatus.PENDING:
            raise api_error(AppError.PROPOSAL_REPORT_NOT_REVIEWABLE, f"status: {report.status.value}")

    @staticmethod
    def accept(db: Session, report_id: int) -> ProposalReportResponse:
        report = ProposalReportService._get_report(db, report_id)
        ProposalReportService._ensure_pending(report)
        proposal = ProposalReportService._get_proposal(db, report.proposal_id)
        if proposal.status not in (*REPORTABLE_PROPOSAL_STATUSES, ProposalStatus.REPORTED):
            raise api_error(AppError.PROPOSAL_NOT_REPORTABLE, f"status: {proposal.status.value}")
        if proposal.status in REPORTABLE_PROPOSAL_STATUSES:
            proposal.status = ProposalStatus.REPORTED
            (
                db.query(Offer)
                .filter(Offer.proposal_id == proposal.id, Offer.status == OfferStatus.WAITING)
                .update({Offer.status: OfferStatus.REJECTED}, synchronize_session=False)
            )
        report.status = ProposalReportStatus.ACCEPTED
        report.reviewed_at = utcnow_naive()
        db.commit()
        db.refresh(report)
        question = db.query(ProposalReportReasonQuestion).filter(ProposalReportReasonQuestion.id == report.reason_question_id).one()
        return ProposalReportService._to_response(report, question.question_text)

    @staticmethod
    def reject(db: Session, report_id: int) -> ProposalReportResponse:
        report = ProposalReportService._get_report(db, report_id)
        ProposalReportService._ensure_pending(report)
        report.status = ProposalReportStatus.REJECTED
        report.reviewed_at = utcnow_naive()
        db.commit()
        db.refresh(report)
        question = db.query(ProposalReportReasonQuestion).filter(ProposalReportReasonQuestion.id == report.reason_question_id).one()
        return ProposalReportService._to_response(report, question.question_text)
