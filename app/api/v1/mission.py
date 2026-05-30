"""Mission API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.mission import MissionStatus
from app.models.user import User
from app.schemas.common import ApiResponse, PageResponse
from app.schemas.mission import MissionResponse, MissionRole, MissionUpdateRequest
from app.services.mission_service import MissionService


router = APIRouter(prefix="/v1/mission", tags=["Mission"])


@router.get(
    "",
    response_model=ApiResponse[PageResponse[MissionResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get current user missions",
)
async def get_missions(
    role: MissionRole = Query(MissionRole.ORDERER),
    status_filter: MissionStatus | None = Query(None, alias="status"),
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
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
    summary="Update mission status",
)
async def update_mission(
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
