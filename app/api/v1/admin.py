"""Admin API endpoints."""
from fastapi import APIRouter, Depends, status
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
from app.services.offer_service import OfferService
from app.services.proposal_service import ProposalService


router = APIRouter(prefix="/admin", tags=["관리자"])


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
