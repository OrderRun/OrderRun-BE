"""Offer API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.errors import AppError
from app.core.firebase import get_notification_worker
from app.core.openapi import (
    OFFER_ACCEPT_EXAMPLE,
    OFFER_CREATE_EXAMPLE,
    OFFER_DELIVERY_EXAMPLE,
    OFFER_DETAIL_EXAMPLES,
    OFFER_DISPUTE_EXAMPLE,
    OFFER_LIST_EXAMPLES,
    OFFER_PAGE_EXAMPLES,
    error_responses,
    no_content_response,
    success_response,
    success_response_examples,
)
from app.core.security import get_current_user
from app.models.offer import OfferStatus
from app.models.user import User
from app.schemas.common import ApiResponse, PageResponse
from app.schemas.offer import OfferAcceptResponse, OfferCreate, OfferDetailResponse, OfferResponse, OfferSummaryResponse
from app.schemas.proof import ProofDeliveryRequest, ProofDisputeRequest
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
    responses={
        201: success_response(OFFER_CREATE_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.VALIDATION_ERROR,
            AppError.OFFER_PROPOSAL_NOT_FOUND,
            AppError.SELF_OFFER_NOT_ALLOWED,
            AppError.PROPOSAL_NOT_OPEN,
            AppError.DUPLICATE_OFFER,
        ),
    },
)
def create_offer(
    offer_data: OfferCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OfferResponse]:
    offer = OfferService.create(db, request=offer_data, runner_id=current_user.id)
    background_tasks.add_task(get_notification_worker().flush_pending, SessionLocal)
    return ApiResponse(success=True, data=offer, message="제안이 제출되었습니다.")


@router.get(
    "/own",
    response_model=ApiResponse[PageResponse[OfferResponse]],
    status_code=status.HTTP_200_OK,
    summary="내 제안 목록 조회",
    description="현재 러너가 등록한 제안 목록을 상태와 페이지 조건으로 조회합니다.",
    responses={
        200: success_response_examples(OFFER_PAGE_EXAMPLES),
        **error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR),
    },
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
    response_model=ApiResponse[list[OfferSummaryResponse]],
    status_code=status.HTTP_200_OK,
    summary="요청별 제안 목록 조회",
    description="특정 요청에 등록된 제안 목록을 조회합니다.",
    responses={
        200: success_response_examples(OFFER_LIST_EXAMPLES),
        **error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR, AppError.OFFER_PROPOSAL_NOT_FOUND),
    },
)
def get_offers(
    proposal_id: int = Query(..., gt=0, alias="proposalId", description="요청 ID"),
    request: OfferSearchRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[OfferSummaryResponse]]:
    offers = OfferService.find_offers_by_proposal(
        db,
        proposal_id=proposal_id,
        offer_statuses=request.statuses,
    )
    return ApiResponse(success=True, data=offers, message="Success")


@router.get(
    "/{id}",
    response_model=ApiResponse[OfferDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="제안 상세 조회",
    description="제안 ID로 제안 상세 정보를 조회합니다.",
    responses={
        200: success_response_examples(OFFER_DETAIL_EXAMPLES),
        **error_responses(AppError.INVALID_TOKEN, AppError.OFFER_NOT_FOUND),
    },
)
def get_offer(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OfferDetailResponse]:
    offer = OfferService.get_offer_detail(db, offer_id=id, viewer_id=current_user.id)
    return ApiResponse(success=True, data=offer, message="Success")


@router.post(
    "/{offer_id}/accept",
    response_model=ApiResponse[OfferAcceptResponse],
    status_code=status.HTTP_201_CREATED,
    summary="제안 수락",
    description="오더러가 제안을 수락하고 요청/제안 상태를 매칭 상태로 전환합니다.",
    responses={
        201: success_response(OFFER_ACCEPT_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.VALIDATION_ERROR,
            AppError.OFFER_NOT_FOUND,
            AppError.FORBIDDEN,
            AppError.OFFER_NOT_ACCEPTABLE,
            AppError.PROPOSAL_NOT_MATCHABLE,
        ),
    },
)
def accept_offer(
    offer_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OfferAcceptResponse]:
    accepted = OfferService.accept(db, offer_id=offer_id, orderer_id=current_user.id)
    background_tasks.add_task(get_notification_worker().flush_pending, SessionLocal)
    return ApiResponse(success=True, data=accepted, message="제안이 수락되었습니다.")


@router.post(
    "/{offer_id}/complete-delivery",
    response_model=ApiResponse[OfferResponse],
    status_code=status.HTTP_200_OK,
    summary="러너 완료 처리",
    description="러너가 완료 증빙 이미지를 등록하고 제안을 완료 상태로 변경합니다.",
    responses={
        200: success_response(OFFER_DELIVERY_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.VALIDATION_ERROR,
            AppError.OFFER_NOT_FOUND,
            AppError.FORBIDDEN,
            AppError.OFFER_NOT_UPDATABLE,
        ),
    },
)
def complete_delivery(
    offer_id: int,
    request: ProofDeliveryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OfferResponse]:
    offer = OfferService.complete_delivery(
        db,
        offer_id=offer_id,
        runner_id=current_user.id,
        proof_image_url=request.proof_image_url,
    )
    background_tasks.add_task(get_notification_worker().flush_pending, SessionLocal)
    return ApiResponse(success=True, data=offer, message="완료 처리되었습니다.")


@router.post(
    "/{offer_id}/dispute",
    response_model=ApiResponse[OfferResponse],
    status_code=status.HTTP_200_OK,
    summary="러너 분쟁 접수",
    description="러너가 수락된 제안의 분쟁을 접수합니다.",
    responses={
        200: success_response(OFFER_DISPUTE_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.VALIDATION_ERROR,
            AppError.OFFER_NOT_FOUND,
            AppError.FORBIDDEN,
            AppError.OFFER_NOT_UPDATABLE,
        ),
    },
)
def raise_offer_dispute(
    offer_id: int,
    request: ProofDisputeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OfferResponse]:
    offer = OfferService.raise_dispute(
        db,
        offer_id=offer_id,
        runner_id=current_user.id,
        dispute_reason=request.dispute_reason,
    )
    return ApiResponse(success=True, data=offer, message="분쟁이 접수되었습니다.")


@router.delete(
    "/{offer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="제안 취소",
    description="현재 러너가 등록한 제안을 취소합니다.",
    responses={
        204: no_content_response("제안 취소 성공"),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.OFFER_NOT_FOUND,
            AppError.FORBIDDEN,
            AppError.OFFER_NOT_CANCELLABLE,
        ),
    },
)
def cancel_offer(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    OfferService.cancel(db, offer_id=offer_id, runner_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
