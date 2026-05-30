"""Settlement API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.settlement import SettlementAccountRequest, SettlementAccountResponse
from app.services.settlement_service import SettlementService


router = APIRouter(prefix="/v1/settlement", tags=["settlement"])


@router.get(
    "/account",
    response_model=ApiResponse[SettlementAccountResponse],
    status_code=status.HTTP_200_OK,
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
)
async def save_settlement_account(
    request: SettlementAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[SettlementAccountResponse]:
    account = SettlementService.save_account(db, user_id=current_user.id, request=request)
    return ApiResponse(success=True, data=account, message="정산 계좌가 저장되었습니다.")
