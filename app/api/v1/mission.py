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
from app.schemas.mission import MissionResponse, MissionRole, MissionUpdateRequest
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


@router.put(
    "/{mission_id}",
    response_model=ApiResponse[MissionResponse],
    status_code=status.HTTP_200_OK,
    summary="미션 상태 변경",
    description="미션 진행 상태를 변경합니다.",
    responses=error_responses(
        AppError.INVALID_TOKEN,
        AppError.VALIDATION_ERROR,
        AppError.MISSION_NOT_FOUND,
        AppError.FORBIDDEN,
        AppError.MISSION_NOT_UPDATABLE,
        AppError.MISSION_PROOF_IMAGE_REQUIRED,
        AppError.MISSION_DISPUTE_REASON_REQUIRED,
    ),
)
def update_mission(
    mission_id: int,
    request: MissionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MissionResponse]:
    mission = MissionService.update_status(
        db,
        mission_id=mission_id,
        user_id=current_user.id,
        request=request,
    )
    return ApiResponse(success=True, data=mission, message="미션 상태가 업데이트되었습니다.")
