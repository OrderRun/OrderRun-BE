"""Admin API router."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.openapi import (
    OFFER_RESOLVED_EXAMPLE,
    PROPOSAL_EXAMPLE,
    PROPOSAL_PAGE_EXAMPLE,
    error_responses,
    success_response,
)
from app.schemas.offer import OfferResponse
from app.schemas.proposal import ProposalResponse
from app.schemas.common import ApiResponse
from app.schemas.common import PageResponse
from app.schemas.proposal_report import ProposalReportResponse
from app.models.proposal_report import ProposalReportStatus
from app.services.offer.offer_service import OfferService
from app.services.proposal.proposal_service import ProposalService
from app.services.proposal.proposal_report_service import ProposalReportService


router = APIRouter(prefix="/admin", tags=["관리자"])


@router.get(
    "/proposal-reports",
    response_model=ApiResponse[PageResponse[ProposalReportResponse]],
    summary="게시글 신고 목록 조회 (관리자 전용)",
    responses={200: success_response({"success": True, "data": {"content": [], "totalElements": 0, "totalPages": 0, "pageNumber": 0, "pageSize": 20, "first": True, "last": True}, "message": None})},
)
def list_proposal_reports(
    report_status: ProposalReportStatus | None = Query(None, alias="status"),
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ApiResponse[PageResponse[ProposalReportResponse]]:
    return ApiResponse(success=True, data=ProposalReportService.list_reports(db, report_status, page, size))


@router.post(
    "/proposal-reports/{report_id}/accept",
    response_model=ApiResponse[ProposalReportResponse],
    summary="게시글 신고 승인 (관리자 전용)",
    responses={
        200: success_response({"success": True, "data": {"id": 1, "proposalId": 1, "reporterId": "550e8400-e29b-41d4-a716-446655440001", "reasonQuestionId": 1, "reasonQuestionText": "광고 또는 스팸이에요", "detailReason": None, "status": "ACCEPTED", "createdAt": "2026-06-01T12:00:00+09:00", "reviewedAt": "2026-06-01T12:10:00+09:00"}, "message": "신고가 승인되었습니다."}),
        **error_responses(AppError.PROPOSAL_REPORT_NOT_FOUND, AppError.PROPOSAL_REPORT_NOT_REVIEWABLE, AppError.PROPOSAL_NOT_REPORTABLE),
    },
)
def accept_proposal_report(report_id: int, db: Session = Depends(get_db)) -> ApiResponse[ProposalReportResponse]:
    return ApiResponse(success=True, data=ProposalReportService.accept(db, report_id), message="신고가 승인되었습니다.")


@router.post(
    "/proposal-reports/{report_id}/reject",
    response_model=ApiResponse[ProposalReportResponse],
    summary="게시글 신고 반려 (관리자 전용)",
    responses={
        200: success_response({"success": True, "data": {"id": 1, "proposalId": 1, "reporterId": "550e8400-e29b-41d4-a716-446655440001", "reasonQuestionId": 1, "reasonQuestionText": "광고 또는 스팸이에요", "detailReason": None, "status": "REJECTED", "createdAt": "2026-06-01T12:00:00+09:00", "reviewedAt": "2026-06-01T12:10:00+09:00"}, "message": "신고가 반려되었습니다."}),
        **error_responses(AppError.PROPOSAL_REPORT_NOT_FOUND, AppError.PROPOSAL_REPORT_NOT_REVIEWABLE),
    },
)
def reject_proposal_report(report_id: int, db: Session = Depends(get_db)) -> ApiResponse[ProposalReportResponse]:
    return ApiResponse(success=True, data=ProposalReportService.reject(db, report_id), message="신고가 반려되었습니다.")


@router.post(
    "/proposal/{proposal_id}/confirm-payment",
    response_model=ApiResponse[ProposalResponse],
    status_code=status.HTTP_200_OK,
    summary="입금 확인 (관리자 전용)",
    description="관리자가 오더러의 입금을 확인하여 제안을 POSTED 상태로 전환합니다.",
    responses={
        200: success_response({"success": True, "data": PROPOSAL_EXAMPLE, "message": None}),
        **error_responses(
            AppError.VALIDATION_ERROR,
            AppError.PROPOSAL_NOT_FOUND,
            AppError.INVALID_STATUS,
        ),
    },
)
def confirm_payment(
    proposal_id: int,
    db: Session = Depends(get_db),
):
    """
    Confirm payment for a proposal.

    Args:
        proposal_id: Proposal ID
        db: Database session

    Returns:
        ApiResponse with updated proposal
    """
    proposal = ProposalService.confirm_payment(
        db=db,
        proposal_id=proposal_id,
    )

    return ApiResponse(
        success=True,
        data=ProposalResponse.model_validate(proposal),
    )


@router.get(
    "/proposal/pending-payment",
    summary="입금 대기 중인 제안 목록 조회 (관리자 전용)",
    description="관리자가 입금 대기 중인 모든 제안을 조회합니다.",
    responses={
        200: success_response(
            {"success": True, "data": PROPOSAL_PAGE_EXAMPLE["data"]["content"], "message": None}
        ),
    },
)
def list_pending_payment_proposals(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Get all proposals with HOLDING status.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of pending payment proposals
    """
    from app.models.proposal import Proposal, ProposalStatus

    proposals = (
        db.query(Proposal)
        .filter(Proposal.status == ProposalStatus.HOLDING)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return ApiResponse(
        success=True,
        data=[ProposalResponse.model_validate(p) for p in proposals],
    )


@router.post(
    "/offer/{offer_id}/resolve",
    response_model=ApiResponse[OfferResponse],
    status_code=status.HTTP_200_OK,
    summary="제안 분쟁 해결 처리 (관리자 전용)",
    description="관리자가 분쟁 제안을 해결 완료 상태로 전환합니다.",
    responses={
        200: success_response(OFFER_RESOLVED_EXAMPLE),
        **error_responses(
            AppError.OFFER_NOT_FOUND,
            AppError.OFFER_NOT_UPDATABLE,
        ),
    },
)
def resolve_offer(
    offer_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[OfferResponse]:
    offer = OfferService.resolve(db, offer_id=offer_id)
    return ApiResponse(success=True, data=offer, message="제안 분쟁이 해결되었습니다.")
