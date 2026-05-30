"""Terms agreement endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.terms import TermsAgreementRequest, TermsAgreementResponse
from app.schemas.user import ApiResponse
from app.services.terms_service import TermsAgreementService


router = APIRouter(prefix="/v1/terms", tags=["terms"])


@router.post(
    "",
    response_model=ApiResponse[TermsAgreementResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
def agree_terms(
    payload: TermsAgreementRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TermsAgreementService(db)
    data = service.agree(current_user, payload)
    return {
        "success": True,
        "data": data.model_dump(by_alias=True),
        "message": "약관 동의가 완료되었습니다.",
    }
