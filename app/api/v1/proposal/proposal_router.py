"""Proposal API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.errors import AppError
from app.core.firebase import get_notification_worker
from app.core.openapi import (
    PROPOSAL_CANCEL_EXAMPLE,
    PROPOSAL_ALL_COMPLETED_RECEIVED_EXAMPLE,
    PROPOSAL_CREATE_EXAMPLE,
    PROPOSAL_DETAIL_EXAMPLES,
    PROPOSAL_DISPUTE_EXAMPLE,
    PROPOSAL_OWN_PAGE_EXAMPLE,
    PROPOSAL_PAGE_EXAMPLE,
    PROPOSAL_RECEIVED_EXAMPLE,
    PROPOSAL_UPDATE_EXAMPLE,
    error_responses,
    success_response,
    success_response_examples,
)
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
from app.schemas.dispute_evidence import DisputeRequest
from app.schemas.proposal_report import ProposalReportCreateRequest, ProposalReportResponse
from app.services.proposal_service import ProposalService
from app.services.proposal_report_service import ProposalReportService


router = APIRouter(prefix="/proposal", tags=["요청"])


class ProposalSearchRequest:
    def __init__(
        self,
        status: list[ProposalStatus] | None = Query(
            None,
            description="요청 상태 필터. 반복 입력 가능: status=A&status=B",
        ),
        page: int = Query(0, ge=0, description="페이지 번호(0부터 시작)"),
        size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    ):
        self.statuses = status
        self.page = page
        self.size = size


@router.get(
    "",
    response_model=ApiResponse[PageResponse[ProposalResponse]],
    status_code=status.HTTP_200_OK,
    summary="공개 요청 목록 조회",
    description="현재 조회 가능한 심부름 요청 목록을 페이지 단위로 조회합니다.",
    responses={
        200: success_response(PROPOSAL_PAGE_EXAMPLE),
        **error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR),
    },
)
def list_proposals(
    request: ProposalSearchRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[PageResponse[ProposalResponse]]:
    page_response = ProposalService.search_proposals(
        db,
        proposal_statuses=request.statuses,
        page=request.page,
        size=request.size,
    )
    return ApiResponse(success=True, data=page_response)


@router.get(
    "/own",
    response_model=ApiResponse[PageResponse[ProposalOwnResponse]],
    status_code=status.HTTP_200_OK,
    summary="내 요청 목록 조회",
    description="현재 사용자가 등록한 요청 목록을 상태와 페이지 조건으로 조회합니다.",
    responses={
        200: success_response(PROPOSAL_OWN_PAGE_EXAMPLE),
        **error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR),
    },
)
def list_own_proposals(
    request: ProposalSearchRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[PageResponse[ProposalOwnResponse]]:
    proposals = ProposalService.search_owner_proposals(
        db,
        user_id=current_user.id,
        proposal_statuses=request.statuses,
        page=request.page,
        size=request.size,
    )
    return ApiResponse(success=True, data=proposals)


@router.get(
    "/{proposal_id}",
    response_model=ApiResponse[ProposalDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="요청 상세 조회",
    description="요청 ID로 심부름 요청 상세 정보를 조회합니다.",
    responses={
        200: success_response_examples(PROPOSAL_DETAIL_EXAMPLES),
        **error_responses(AppError.INVALID_TOKEN, AppError.PROPOSAL_NOT_FOUND),
    },
)
def get_proposal(
    proposal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProposalDetailResponse]:
    proposal = ProposalService.get_proposal_detail(db, proposal_id, current_user.id)
    return ApiResponse(success=True, data=proposal)


@router.post(
    "/{proposal_id}/reports",
    response_model=ApiResponse[ProposalReportResponse],
    status_code=status.HTTP_201_CREATED,
    summary="요청 게시글 신고",
    description="공개 모집 중인 다른 사용자의 요청 게시글을 신고합니다.",
    responses={
        201: success_response({"success": True, "data": {"id": 1, "proposalId": 1, "reporterId": "550e8400-e29b-41d4-a716-446655440001", "reasonQuestionId": 1, "reasonQuestionText": "광고 또는 스팸이에요", "detailReason": "반복 광고입니다.", "status": "PENDING", "createdAt": "2026-06-01T12:00:00+09:00", "reviewedAt": None}, "message": "신고가 접수되었습니다."}),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.VALIDATION_ERROR,
            AppError.PROPOSAL_NOT_FOUND,
            AppError.PROPOSAL_NOT_REPORTABLE,
            AppError.PROPOSAL_SELF_REPORT_NOT_ALLOWED,
            AppError.DUPLICATE_PROPOSAL_REPORT,
        ),
    },
)
def create_proposal_report(
    proposal_id: int,
    request: ProposalReportCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProposalReportResponse]:
    report = ProposalReportService.create(db, proposal_id, current_user.id, request)
    return ApiResponse(success=True, data=report, message="신고가 접수되었습니다.")


@router.post(
    "",
    response_model=ApiResponse[ProposalResponse],
    status_code=status.HTTP_201_CREATED,
    summary="요청 등록",
    description="새 심부름 요청을 등록합니다.",
    responses={
        201: success_response(PROPOSAL_CREATE_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.VALIDATION_ERROR,
            AppError.USER_NOT_FOUND,
            AppError.INVALID_DATE_TIME_FORMAT,
            AppError.PROPOSAL_DEADLINE_INVALID,
            AppError.PROPOSAL_ERRAND_FEE_INVALID,
        ),
    },
)
def create_proposal(
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
    summary="요청 수정",
    description="본인이 등록한 요청을 수정합니다.",
    responses={
        200: success_response(PROPOSAL_UPDATE_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.VALIDATION_ERROR,
            AppError.PROPOSAL_NOT_FOUND,
            AppError.FORBIDDEN,
            AppError.PROPOSAL_NOT_EDITABLE,
            AppError.INVALID_DATE_TIME_FORMAT,
            AppError.PROPOSAL_DEADLINE_INVALID,
            AppError.PROPOSAL_ERRAND_FEE_INVALID,
        ),
    },
)
def update_proposal(
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
    summary="요청 취소",
    description="본인이 등록한 요청을 취소합니다.",
    responses={
        200: success_response(PROPOSAL_CANCEL_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.PROPOSAL_NOT_FOUND,
            AppError.FORBIDDEN,
            AppError.PROPOSAL_NOT_CANCELLABLE,
        ),
    },
)
def cancel_proposal(
    proposal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProposalResponse]:
    proposal = ProposalService.cancel(db, proposal_id=proposal_id, orderer_id=current_user.id)
    return ApiResponse(success=True, data=proposal, message="제안이 취소되었습니다.")


@router.post(
    "/{proposal_id}/confirm-received",
    response_model=ApiResponse[ProposalDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="오더러 완료 처리",
    description="오더러가 완료를 확인하고 요청을 완료 상태로 변경합니다.",
    responses={
        200: success_response_examples(
            {
                "order_completed": PROPOSAL_RECEIVED_EXAMPLE,
                "all_completed": PROPOSAL_ALL_COMPLETED_RECEIVED_EXAMPLE,
            }
        ),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.PROPOSAL_NOT_FOUND,
            AppError.OFFER_NOT_FOUND,
            AppError.FORBIDDEN,
            AppError.PROPOSAL_NOT_UPDATABLE,
        ),
    },
)
def confirm_received(
    proposal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProposalDetailResponse]:
    proposal = ProposalService.confirm_received(db, proposal_id=proposal_id, orderer_id=current_user.id)
    return ApiResponse(success=True, data=proposal, message="완료 확인되었습니다.")


@router.post(
    "/{proposal_id}/dispute",
    response_model=ApiResponse[ProposalDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="오더 분쟁 접수",
    description="오더러가 요청의 분쟁을 접수합니다.",
    responses={
        200: success_response(PROPOSAL_DISPUTE_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.VALIDATION_ERROR,
            AppError.PROPOSAL_NOT_FOUND,
            AppError.OFFER_NOT_FOUND,
            AppError.FORBIDDEN,
            AppError.PROPOSAL_NOT_UPDATABLE,
        ),
    },
)
def raise_proposal_dispute(
    proposal_id: int,
    request: DisputeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProposalDetailResponse]:
    proposal = ProposalService.raise_dispute(
        db,
        proposal_id=proposal_id,
        orderer_id=current_user.id,
        survey_question_id=request.survey_question_id,
        dispute_reason=request.dispute_reason,
    )
    background_tasks.add_task(get_notification_worker().flush_pending, SessionLocal)
    return ApiResponse(success=True, data=proposal, message="분쟁이 접수되었습니다.")
