"""Mission API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.openapi import AUTH_ERROR_RESPONSES, error_responses
from app.core.security import get_current_user
from app.models.mission import MissionStatus
from app.models.user import User
from app.schemas.common import ApiResponse, PageResponse
from app.schemas.mission import (
    MissionCompleteDeliveryRequest,
    MissionDisputeRequest,
    MissionResponse,
    MissionRole
)
from app.services.mission_service import MissionService


router = APIRouter(prefix="/v1/mission", tags=["미션"])


@router.get(
    "",
    response_model=ApiResponse[PageResponse[MissionResponse]],
    status_code=status.HTTP_200_OK,
    summary="내 미션 목록 조회",
    description="현재 사용자의 미션 목록을 역할, 상태, 페이지 조건으로 조회합니다.",
    responses=AUTH_ERROR_RESPONSES,
)
def get_missions(
    role: MissionRole = Query(MissionRole.ORDERER, description="조회 역할"),
    status_filter: MissionStatus | None = Query(None, alias="status", description="미션 상태 필터"),
    page: int = Query(0, ge=0, description="페이지 번호(0부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[PageResponse[MissionResponse]]:
    missions = MissionService.list_own(
        db,
        user_id=current_user.id,
        role=role,
        mission_status=status_filter,
        page=page,
        size=size,
    )
    return ApiResponse(success=True, data=missions, message="Success")


@router.post(
    "/{mission_id}/complete-delivery",
    response_model=ApiResponse[MissionResponse],
    status_code=status.HTTP_200_OK,
    summary="전달 완료",
    description="러너가 전달 완료 증빙 이미지를 등록하고 미션을 전달 완료 상태로 변경합니다.",
    responses=error_responses(
        AppError.INVALID_TOKEN,
        AppError.VALIDATION_ERROR,
        AppError.MISSION_NOT_FOUND,
        AppError.FORBIDDEN,
        AppError.MISSION_NOT_UPDATABLE,
    ),
)
def complete_delivery(
    mission_id: int,
    request: MissionCompleteDeliveryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MissionResponse]:
    mission = MissionService.complete_delivery(
        db,
        mission_id=mission_id,
        runner_id=current_user.id,
        proof_image_url=request.proof_image_url,
    )
    return ApiResponse(success=True, data=mission, message="전달 완료되었습니다.")


@router.post(
    "/{mission_id}/confirm-received",
    response_model=ApiResponse[MissionResponse],
    status_code=status.HTTP_200_OK,
    summary="수령 확인",
    description="오더러가 수령을 확인하고 미션을 완료 상태로 변경합니다.",
    responses=error_responses(
        AppError.INVALID_TOKEN,
        AppError.MISSION_NOT_FOUND,
        AppError.FORBIDDEN,
        AppError.MISSION_NOT_UPDATABLE,
    ),
)
def confirm_received(
    mission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MissionResponse]:
    mission = MissionService.confirm_received(db, mission_id=mission_id, orderer_id=current_user.id)
    return ApiResponse(success=True, data=mission, message="수령 확인되었습니다.")


@router.post(
    "/{mission_id}/dispute",
    response_model=ApiResponse[MissionResponse],
    status_code=status.HTTP_200_OK,
    summary="분쟁 접수",
    description="오더러 또는 러너가 미션 분쟁을 접수합니다.",
    responses=error_responses(
        AppError.INVALID_TOKEN,
        AppError.VALIDATION_ERROR,
        AppError.MISSION_NOT_FOUND,
        AppError.FORBIDDEN,
        AppError.MISSION_NOT_UPDATABLE,
    ),
)
def raise_dispute(
    mission_id: int,
    request: MissionDisputeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MissionResponse]:
    mission = MissionService.raise_dispute(
        db,
        mission_id=mission_id,
        user_id=current_user.id,
        dispute_reason=request.dispute_reason,
    )
    return ApiResponse(success=True, data=mission, message="분쟁이 접수되었습니다.")
