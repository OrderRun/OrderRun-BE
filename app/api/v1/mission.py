"""Mission API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.firebase import get_notification_worker
from app.core.errors import AppError
from app.core.openapi import (
    MISSION_DELIVERY_EXAMPLE,
    MISSION_DISPUTE_EXAMPLE,
    MISSION_RECEIVED_EXAMPLE,
    error_responses,
    success_response,
    success_response_examples,
)
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.mission import (
    MissionCompleteDeliveryRequest,
    MissionDisputeRequest,
    MissionResponse,
    MissionUpdateRequest,
)
from app.services.mission_service import MissionService


router = APIRouter(prefix="/v1/mission", tags=["미션"])


@router.post(
    "/{mission_id}/complete-delivery",
    response_model=ApiResponse[MissionResponse],
    status_code=status.HTTP_200_OK,
    summary="전달 완료",
    description="러너가 전달 완료 증빙 이미지를 등록하고 미션을 전달 완료 상태로 변경합니다.",
    responses={
        200: success_response(MISSION_DELIVERY_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.VALIDATION_ERROR,
            AppError.MISSION_NOT_FOUND,
            AppError.FORBIDDEN,
            AppError.MISSION_NOT_UPDATABLE,
        ),
    },
)
def complete_delivery(
    mission_id: int,
    request: MissionCompleteDeliveryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MissionResponse]:
    mission = MissionService.complete_delivery(
        db,
        mission_id=mission_id,
        runner_id=current_user.id,
        proof_image_url=request.proof_image_url,
    )
    background_tasks.add_task(get_notification_worker().flush_pending, SessionLocal)
    return ApiResponse(success=True, data=mission, message="전달 완료되었습니다.")


@router.put(
    "/{mission_id}",
    response_model=ApiResponse[MissionResponse],
    status_code=status.HTTP_200_OK,
    summary="미션 상태 업데이트",
    description="기존 클라이언트를 위한 미션 상태 업데이트 API입니다. 신규 클라이언트는 액션별 API를 사용합니다.",
    responses={
        200: success_response_examples(
            {
                "complete_delivery": MISSION_DELIVERY_EXAMPLE,
                "confirm_received": MISSION_RECEIVED_EXAMPLE,
                "dispute": MISSION_DISPUTE_EXAMPLE,
            }
        ),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.VALIDATION_ERROR,
            AppError.MISSION_NOT_FOUND,
            AppError.FORBIDDEN,
            AppError.MISSION_NOT_UPDATABLE,
        ),
    },
)
def update_mission(
    mission_id: int,
    request: MissionUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MissionResponse]:
    mission = MissionService.update_status(db, mission_id=mission_id, user_id=current_user.id, request=request)
    background_tasks.add_task(get_notification_worker().flush_pending, SessionLocal)
    messages = {
        "COMPLETE_DELIVERY": "전달 완료되었습니다.",
        "CONFIRM_RECEIVED": "수령 확인되었습니다.",
        "DISPUTE": "분쟁이 접수되었습니다.",
    }
    return ApiResponse(success=True, data=mission, message=messages[request.action.value])


@router.post(
    "/{mission_id}/confirm-received",
    response_model=ApiResponse[MissionResponse],
    status_code=status.HTTP_200_OK,
    summary="수령 확인",
    description="오더러가 수령을 확인하고 미션을 완료 상태로 변경합니다.",
    responses={
        200: success_response(MISSION_RECEIVED_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.MISSION_NOT_FOUND,
            AppError.FORBIDDEN,
            AppError.MISSION_NOT_UPDATABLE,
        ),
    },
)
def confirm_received(
    mission_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MissionResponse]:
    mission = MissionService.confirm_received(db, mission_id=mission_id, orderer_id=current_user.id)
    background_tasks.add_task(get_notification_worker().flush_pending, SessionLocal)
    return ApiResponse(success=True, data=mission, message="수령 확인되었습니다.")


@router.post(
    "/{mission_id}/dispute",
    response_model=ApiResponse[MissionResponse],
    status_code=status.HTTP_200_OK,
    summary="분쟁 접수",
    description="오더러 또는 러너가 미션 분쟁을 접수합니다.",
    responses={
        200: success_response(MISSION_DISPUTE_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.VALIDATION_ERROR,
            AppError.MISSION_NOT_FOUND,
            AppError.FORBIDDEN,
            AppError.MISSION_NOT_UPDATABLE,
        ),
    },
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
