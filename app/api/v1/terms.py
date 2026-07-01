"""Terms agreement endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.openapi import TERMS_AGREEMENT_EXAMPLE, error_responses, success_response
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.terms import TermsAgreementRequest, TermsAgreementResponse
from app.schemas.user import ApiResponse
from app.services.terms_service import TermsAgreementService


router = APIRouter(prefix="/v1/terms", tags=["약관"])


@router.post(
    "",
    response_model=ApiResponse[TermsAgreementResponse],
    status_code=status.HTTP_201_CREATED,
    summary="약관 동의 저장",
    description="필수 약관 동의 여부를 저장합니다.",
    responses={
        201: success_response(TERMS_AGREEMENT_EXAMPLE),
        **error_responses(
            AppError.INVALID_TOKEN,
            AppError.VALIDATION_ERROR,
            AppError.USER_NOT_FOUND,
            AppError.REQUIRED_TERMS_INVALID,
        ),
    },
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
