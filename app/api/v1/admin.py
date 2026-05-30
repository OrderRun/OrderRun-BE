"""Admin API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.proposal import ProposalResponse
from app.schemas.common import ApiResponse
from app.services.proposal import ProposalService


router = APIRouter(prefix="/admin", tags=["Admin"])


class PaymentConfirmRequest(BaseModel):
    """Request schema for payment confirmation."""
    depositor_name: Optional[str] = None


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to verify admin user.

    TODO: Implement proper role-based access control.
    For now, this is a placeholder that should be replaced with actual admin role check.
    """
    # TODO: Check if user has admin role
    # if not current_user.is_admin:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="관리자 권한이 필요합니다."
    #     )
    return current_user


@router.post(
    "/proposal/{proposal_id}/confirm-payment",
    response_model=ApiResponse[ProposalResponse],
    status_code=status.HTTP_200_OK,
    summary="입금 확인 (관리자 전용)",
    description="관리자가 오더러의 입금을 확인하여 제안을 POSTED 상태로 전환합니다.",
)
async def confirm_payment(
    proposal_id: int,
    request: PaymentConfirmRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """
    Confirm payment for a proposal.

    Args:
        proposal_id: Proposal ID
        request: Payment confirmation request with optional depositor name
        db: Database session
        admin_user: Current admin user

    Returns:
        ApiResponse with updated proposal
    """
    proposal = ProposalService.confirm_payment(
        db=db,
        proposal_id=proposal_id,
        admin_id=admin_user.id,
        depositor_name=request.depositor_name,
    )

    return ApiResponse(
        success=True,
        data=ProposalResponse.model_validate(proposal),
    )


@router.get(
    "/proposal/pending-payment",
    summary="입금 대기 중인 제안 목록 조회 (관리자 전용)",
    description="관리자가 입금 대기 중인 모든 제안을 조회합니다.",
)
async def list_pending_payment_proposals(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """
    Get all proposals with HOLDING status.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        admin_user: Current admin user

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
