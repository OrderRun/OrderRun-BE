"""Dispute evidence API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError, api_error
from app.core.openapi import DISPUTE_EVIDENCE_EXAMPLE, error_responses, success_response
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.dispute_evidence import DisputeEvidenceResponse
from app.services.dispute.dispute_evidence_service import DisputeEvidenceService


router = APIRouter(prefix="/dispute-evidence", tags=["분쟁 증빙"])


@router.get(
    "",
    response_model=ApiResponse[DisputeEvidenceResponse],
    status_code=status.HTTP_200_OK,
    summary="분쟁 증빙 상세 조회",
    description="거래 당사자가 proposalId 또는 offerId로 분쟁 증빙을 조회합니다.",
    responses={
        200: success_response(DISPUTE_EVIDENCE_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.VALIDATION_ERROR,
            AppError.FORBIDDEN,
            AppError.DISPUTE_EVIDENCE_NOT_FOUND,
        ),
    },
)
def get_dispute_evidence(
    proposal_id: int | None = Query(None, gt=0, alias="proposalId", description="Proposal ID"),
    offer_id: int | None = Query(None, gt=0, alias="offerId", description="Offer ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[DisputeEvidenceResponse]:
    if (proposal_id is None) == (offer_id is None):
        raise api_error(AppError.VALIDATION_ERROR, "proposalId 또는 offerId 중 정확히 하나만 입력해야 합니다.")

    evidence = (
        DisputeEvidenceService.get_by_proposal_id(db, proposal_id, current_user.id)
        if proposal_id is not None
        else DisputeEvidenceService.get_by_offer_id(db, offer_id, current_user.id)
    )
    return ApiResponse(success=True, data=evidence, message="Success")
