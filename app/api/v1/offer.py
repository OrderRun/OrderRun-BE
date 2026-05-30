"""Offer API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.offer import OfferStatus
from app.models.user import User
from app.schemas.common import ApiResponse, PageResponse
from app.schemas.offer import OfferAcceptRequest, OfferAcceptResponse, OfferCreate, OfferResponse
from app.services.offer_service import OfferService


router = APIRouter(prefix="/v1/offer", tags=["Offer"])


@router.post(
    "",
    response_model=ApiResponse[OfferResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new offer",
)
async def create_offer(
    offer_data: OfferCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OfferResponse]:
    offer = OfferService.create(db, request=offer_data, runner_id=current_user.id)
    return ApiResponse(success=True, data=offer, message="제안이 제출되었습니다.")


@router.get(
    "/own",
    response_model=ApiResponse[PageResponse[OfferResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get current runner offers",
)
async def get_own_offers(
    status_filter: OfferStatus | None = Query(None, alias="status"),
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[PageResponse[OfferResponse]]:
    page_response = OfferService.list_own(
        db,
        runner_id=current_user.id,
        offer_status=status_filter,
        page=page,
        size=size,
    )
    return ApiResponse(success=True, data=page_response, message="Success")


@router.get(
    "",
    response_model=ApiResponse[list[OfferResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get offers by proposal",
)
async def get_offers(
    proposal_id: int = Query(..., gt=0, alias="proposalId"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[OfferResponse]]:
    offers = OfferService.list_by_proposal(db, proposal_id=proposal_id, user_id=current_user.id)
    return ApiResponse(success=True, data=offers, message="Success")


@router.get(
    "/{offer_id}",
    response_model=ApiResponse[OfferResponse],
    status_code=status.HTTP_200_OK,
    summary="Get offer detail",
)
async def get_offer(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OfferResponse]:
    offer = OfferService.get_detail(db, offer_id=offer_id, user_id=current_user.id)
    return ApiResponse(success=True, data=offer, message="Success")


@router.post(
    "/{offer_id}/accept",
    response_model=ApiResponse[OfferAcceptResponse],
    status_code=status.HTTP_200_OK,
    summary="Accept offer and create mission",
)
async def accept_offer(
    offer_id: int,
    request: OfferAcceptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OfferAcceptResponse]:
    accepted = OfferService.accept(db, offer_id=offer_id, orderer_id=current_user.id, request=request)
    return ApiResponse(success=True, data=accepted, message="제안이 수락되었습니다.")


@router.delete(
    "/{offer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel current runner offer",
)
async def cancel_offer(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    OfferService.cancel(db, offer_id=offer_id, runner_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
