"""Admin API endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.openapi import (
    MISSION_REFUNDED_EXAMPLE,
    MISSION_SETTLED_EXAMPLE,
    PROPOSAL_EXAMPLE,
    PROPOSAL_PAGE_EXAMPLE,
    error_responses,
    success_response,
)
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.mission import MissionResponse
from app.schemas.proposal import ProposalResponse
from app.schemas.common import ApiResponse
from app.services.mission_service import MissionService
from app.services.proposal_service import ProposalService


router = APIRouter(prefix="/admin", tags=["관리자"])


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to verify admin user.

    TODO: Implement proper role-based access control.
    For now, this is a placeholder that should be replaced with actual admin role check.
    """
    # TODO: Check if user has admin role and raise a centralized API error.
    return current_user


@router.post(
    "/proposal/{proposal_id}/confirm-payment",
    response_model=ApiResponse[ProposalResponse],
    status_code=status.HTTP_200_OK,
    summary="입금 확인 (관리자 전용)",
    description="관리자가 오더러의 입금을 확인하여 제안을 POSTED 상태로 전환합니다.",
    responses={
        200: success_response({"success": True, "data": PROPOSAL_EXAMPLE, "message": None}),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.VALIDATION_ERROR,
            AppError.PROPOSAL_NOT_FOUND,
            AppError.INVALID_STATUS,
        ),
    },
)
def confirm_payment(
    proposal_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """
    Confirm payment for a proposal.

    Args:
        proposal_id: Proposal ID
        db: Database session
        admin_user: Current admin user

    Returns:
        ApiResponse with updated proposal
    """
    _ = admin_user
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
        **error_responses(AppError.INVALID_TOKEN),
    },
)
def list_pending_payment_proposals(
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
    _ = admin_user
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
    "/mission/{mission_id}/confirm-settlement",
    response_model=ApiResponse[MissionResponse],
    status_code=status.HTTP_200_OK,
    summary="미션 정산 완료 처리 (관리자 전용)",
    description="관리자가 러너 정산 입금을 확인하여 미션을 SETTLED 상태로 전환합니다.",
    responses={
        200: success_response(MISSION_SETTLED_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.MISSION_NOT_FOUND,
            AppError.MISSION_NOT_UPDATABLE,
        ),
    },
)
def confirm_mission_settlement(
    mission_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
) -> ApiResponse[MissionResponse]:
    _ = admin_user
    mission = MissionService.confirm_settlement(db, mission_id=mission_id)
    return ApiResponse(success=True, data=mission, message="미션 정산이 완료되었습니다.")


@router.post(
    "/mission/{mission_id}/refund",
    response_model=ApiResponse[MissionResponse],
    status_code=status.HTTP_200_OK,
    summary="미션 환불 완료 처리 (관리자 전용)",
    description="관리자가 분쟁 미션을 환불 완료 상태로 전환합니다.",
    responses={
        200: success_response(MISSION_REFUNDED_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.MISSION_NOT_FOUND,
            AppError.MISSION_NOT_UPDATABLE,
        ),
    },
)
def refund_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
) -> ApiResponse[MissionResponse]:
    _ = admin_user
    mission = MissionService.refund_mission(db, mission_id=mission_id)
    return ApiResponse(success=True, data=mission, message="미션 환불이 완료되었습니다.")
