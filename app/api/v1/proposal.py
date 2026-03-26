from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import ValidationError

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.proposal import ProposalCreate, ProposalResponse
from app.schemas.common import ApiResponse, ErrorResponse, ErrorDetail
from app.services.proposal import ProposalService
from datetime import datetime, timezone

router = APIRouter(prefix="/proposal", tags=["proposal"])


@router.get(
    "",
    response_model=ApiResponse[List[ProposalResponse]],
    status_code=status.HTTP_200_OK,
    summary="전체 제안 목록 조회",
    description="모든 제안 목록을 조회합니다. 인증이 필요하지 않습니다.",
)
async def get_proposals(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get all proposals."""
    proposals = ProposalService.get_all_proposals(db, skip=skip, limit=limit)

    return ApiResponse(
        success=True,
        data=[ProposalResponse.model_validate(p) for p in proposals],
    )


@router.get(
    "/{proposal_id}",
    response_model=ApiResponse[ProposalResponse],
    status_code=status.HTTP_200_OK,
    summary="제안 상세 조회",
    description="특정 제안의 상세 정보를 조회합니다.",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "제안을 찾을 수 없음",
        }
    },
)
async def get_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
):
    """Get proposal by ID."""
    proposal = ProposalService.get_proposal_by_id(db, proposal_id)
    return ApiResponse(
        success=True,
        data=ProposalResponse.model_validate(proposal),
    )


@router.post(
    "",
    response_model=ApiResponse[ProposalResponse],
    status_code=status.HTTP_201_CREATED,
    summary="제안 생성",
    description="새로운 제안을 생성합니다. JWT 인증이 필요합니다.",
    responses={
        400: {
            "model": ErrorResponse,
            "description": "유효성 검증 실패",
        },
        401: {
            "model": ErrorResponse,
            "description": "인증 실패",
        },
    },
)
async def create_proposal(
    proposal_data: ProposalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new proposal."""
    proposal = ProposalService.create_proposal(
        db=db,
        proposal_data=proposal_data,
        orderer_id=current_user.id,
    )

    return ApiResponse(
        success=True,
        data=ProposalResponse.model_validate(proposal),
    )
