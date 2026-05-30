"""Proposal API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.proposal import ProposalStatus
from app.models.user import User
from app.schemas.common import ApiResponse, PageResponse
from app.schemas.proposal import (
    ProposalDetailResponse,
    ProposalOwnResponse,
    ProposalRequest,
    ProposalResponse,
)
from app.services.proposal import ProposalService


router = APIRouter(prefix="/v1/proposal", tags=["proposal"])


@router.get(
    "",
    response_model=ApiResponse[PageResponse[ProposalResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_proposals(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[PageResponse[ProposalResponse]]:
    page_response = ProposalService.list_public(db, page=page, size=size)
    return ApiResponse(success=True, data=page_response)


@router.get(
    "/own",
    response_model=ApiResponse[PageResponse[ProposalOwnResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_own_proposals(
    status_filter: ProposalStatus | None = Query(None, alias="status"),
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[PageResponse[ProposalOwnResponse]]:
    proposals = ProposalService.list_own(
        db,
        user_id=current_user.id,
        proposal_status=status_filter,
        page=page,
        size=size,
    )
    return ApiResponse(success=True, data=proposals)


@router.get(
    "/{proposal_id}",
    response_model=ApiResponse[ProposalDetailResponse],
    status_code=status.HTTP_200_OK,
)
async def get_proposal(
    proposal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProposalDetailResponse]:
    proposal = ProposalService.get_detail(db, proposal_id)
    return ApiResponse(success=True, data=proposal)


@router.post(
    "",
    response_model=ApiResponse[ProposalResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_proposal(
    request: ProposalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProposalResponse]:
    proposal = ProposalService.create(db, request=request, orderer_id=current_user.id)
    return ApiResponse(success=True, data=proposal, message="요청이 등록되었습니다.")


@router.put(
    "/{proposal_id}",
    response_model=ApiResponse[ProposalResponse],
    status_code=status.HTTP_200_OK,
)
async def update_proposal(
    proposal_id: int,
    request: ProposalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProposalResponse]:
    proposal = ProposalService.update(db, proposal_id=proposal_id, request=request, orderer_id=current_user.id)
    return ApiResponse(success=True, data=proposal, message="제안이 수정되었습니다.")


@router.post(
    "/{proposal_id}/cancel",
    response_model=ApiResponse[ProposalResponse],
    status_code=status.HTTP_200_OK,
)
async def cancel_proposal(
    proposal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProposalResponse]:
    proposal = ProposalService.cancel(db, proposal_id=proposal_id, orderer_id=current_user.id)
    return ApiResponse(success=True, data=proposal, message="제안이 취소되었습니다.")
