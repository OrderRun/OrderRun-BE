"""Offer API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.openapi import AUTH_ERROR_RESPONSES, error_responses
from app.core.security import get_current_user
from app.models.offer import OfferStatus
from app.models.user import User
from app.schemas.common import ApiResponse, PageResponse
from app.schemas.offer import OfferAcceptResponse, OfferCreate, OfferResponse
from app.services.offer_service import OfferService


router = APIRouter(prefix="/v1/offer", tags=["제안"])


class OfferSearchRequest:
    def __init__(
        self,
        status: list[OfferStatus] | None = Query(
            None,
            description="제안 상태 필터. 반복 입력 가능: status=A&status=B",
        ),
    ):
        self.statuses = status


class OfferOwnerSearchRequest:
    def __init__(
        self,
        status: list[OfferStatus] | None = Query(
            None,
            description="제안 상태 필터. 반복 입력 가능: status=A&status=B",
        ),
        page: int = Query(0, ge=0, description="페이지 번호(0부터 시작)"),
        size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    ):
        self.statuses = status
        self.page = page
        self.size = size


@router.post(
    "",
    response_model=ApiResponse[OfferResponse],
    status_code=status.HTTP_201_CREATED,
    summary="러너 제안 등록",
    description="러너가 요청에 수행 제안을 등록합니다.",
    responses=error_responses(
        AppError.INVALID_TOKEN,
        AppError.VALIDATION_ERROR,
        AppError.OFFER_PROPOSAL_NOT_FOUND,
        AppError.SELF_OFFER_NOT_ALLOWED,
        AppError.PROPOSAL_NOT_OPEN,
        AppError.DUPLICATE_OFFER,
    ),
)
def create_offer(
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
    summary="내 제안 목록 조회",
    description="현재 러너가 등록한 제안 목록을 상태와 페이지 조건으로 조회합니다.",
    responses=AUTH_ERROR_RESPONSES,
)
def get_own_offers(
    request: OfferOwnerSearchRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[PageResponse[OfferResponse]]:
    page_response = OfferService.search_runner_offers(
        db,
        runner_id=current_user.id,
        offer_statuses=request.statuses,
        page=request.page,
        size=request.size,
    )
    return ApiResponse(success=True, data=page_response, message="Success")


@router.get(
    "",
    response_model=ApiResponse[list[OfferResponse]],
    status_code=status.HTTP_200_OK,
    summary="요청별 제안 목록 조회",
    description="특정 요청에 등록된 제안 목록을 조회합니다.",
    responses=error_responses(AppError.INVALID_TOKEN, AppError.OFFER_PROPOSAL_NOT_FOUND),
)
def get_offers(
    proposal_id: int = Query(..., gt=0, alias="proposalId", description="요청 ID"),
    request: OfferSearchRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[OfferResponse]]:
    offers = OfferService.find_offers_by_proposal(
        db,
        proposal_id=proposal_id,
        offer_statuses=request.statuses,
    )
    return ApiResponse(success=True, data=offers, message="Success")


@router.get(
    "/{offer_id}",
    response_model=ApiResponse[OfferResponse],
    status_code=status.HTTP_200_OK,
    summary="제안 상세 조회",
    description="제안 ID로 제안 상세 정보를 조회합니다.",
    responses=error_responses(AppError.INVALID_TOKEN, AppError.OFFER_NOT_FOUND, AppError.FORBIDDEN),
)
def get_offer(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OfferResponse]:
    offer = OfferService.get_offer_detail(db, offer_id=offer_id, user_id=current_user.id)
    return ApiResponse(success=True, data=offer, message="Success")


@router.post(
    "/{offer_id}/accept",
    response_model=ApiResponse[OfferAcceptResponse],
    status_code=status.HTTP_201_CREATED,
    summary="제안 수락",
    description="오더러가 제안을 수락하고 미션을 생성합니다.",
    responses=error_responses(
        AppError.INVALID_TOKEN,
        AppError.VALIDATION_ERROR,
        AppError.OFFER_NOT_FOUND,
        AppError.FORBIDDEN,
        AppError.MISSION_ALREADY_EXISTS,
        AppError.OFFER_NOT_ACCEPTABLE,
        AppError.PROPOSAL_NOT_MATCHABLE,
    ),
)
def accept_offer(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OfferAcceptResponse]:
    accepted = OfferService.accept(db, offer_id=offer_id, orderer_id=current_user.id)
    return ApiResponse(success=True, data=accepted, message="제안이 수락되었습니다.")


@router.delete(
    "/{offer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="제안 취소",
    description="현재 러너가 등록한 제안을 취소합니다.",
    responses=error_responses(
        AppError.INVALID_TOKEN,
        AppError.OFFER_NOT_FOUND,
        AppError.FORBIDDEN,
        AppError.OFFER_NOT_CANCELLABLE,
    ),
)
def cancel_offer(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    OfferService.cancel(db, offer_id=offer_id, runner_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
