"""Settlement API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.openapi import error_responses
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.settlement import SettlementAccountRequest, SettlementAccountResponse
from app.services.settlement_service import SettlementService


router = APIRouter(prefix="/v1/settlement", tags=["정산"])


@router.get(
    "/account",
    response_model=ApiResponse[SettlementAccountResponse],
    status_code=status.HTTP_200_OK,
    summary="정산 계좌 조회",
    description="현재 사용자의 정산 계좌 정보를 조회합니다.",
    responses=error_responses(AppError.INVALID_TOKEN),
)
async def get_settlement_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[SettlementAccountResponse]:
    account = SettlementService.get_account(db, user_id=current_user.id)
    return ApiResponse(success=True, data=account, message="Success")


@router.put(
    "/account",
    response_model=ApiResponse[SettlementAccountResponse],
    status_code=status.HTTP_200_OK,
    summary="정산 계좌 저장",
    description="현재 사용자의 정산 계좌 정보를 저장하거나 갱신합니다.",
    responses=error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR),
)
async def save_settlement_account(
    request: SettlementAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[SettlementAccountResponse]:
    account = SettlementService.save_account(db, user_id=current_user.id, request=request)
    return ApiResponse(success=True, data=account, message="정산 계좌가 저장되었습니다.")
