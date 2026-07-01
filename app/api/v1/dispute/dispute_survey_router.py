"""Dispute survey API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.openapi import DISPUTE_SURVEY_QUESTIONS_EXAMPLE, error_responses, success_response
from app.core.security import get_current_user
from app.models.dispute_survey import DisputeSurveyTargetType
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.dispute_survey import DisputeSurveyQuestionResponse
from app.services.dispute.dispute_survey_service import DisputeSurveyService


router = APIRouter(prefix="/dispute-survey", tags=["분쟁 설문"])


@router.get(
    "/questions",
    response_model=ApiResponse[list[DisputeSurveyQuestionResponse]],
    status_code=status.HTTP_200_OK,
    summary="분쟁 설문 질문 조회",
    description="분쟁 접수 전에 클라이언트가 표시할 설문 질문 목록을 대상별로 조회합니다.",
    responses={
        200: success_response(DISPUTE_SURVEY_QUESTIONS_EXAMPLE),
        **error_responses(AppError.INVALID_TOKEN, AppError.VALIDATION_ERROR),
    },
)
def list_dispute_survey_questions(
    target_type: DisputeSurveyTargetType = Query(..., alias="targetType", description="질문 대상: ORDER 또는 RUNNER"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[DisputeSurveyQuestionResponse]]:
    _ = current_user
    questions = DisputeSurveyService.list_questions(db, target_type)
    return ApiResponse(success=True, data=questions, message="Success")
