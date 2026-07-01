"""Proposal report reason API endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.openapi import error_responses, success_response
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.proposal_report import ProposalReportReasonQuestionResponse
from app.services.proposal_report_service import ProposalReportService


router = APIRouter(prefix="/proposal-report-reasons", tags=["게시글 신고"])


@router.get(
    "",
    response_model=ApiResponse[list[ProposalReportReasonQuestionResponse]],
    status_code=status.HTTP_200_OK,
    summary="게시글 신고 사유 조회",
    description="게시글 신고 화면에 표시할 활성 신고 사유를 조회합니다.",
    responses={
        200: success_response({"success": True, "data": [{"id": 1, "questionText": "광고 또는 스팸이에요", "displayOrder": 1}], "message": "Success"}),
        **error_responses(AppError.INVALID_TOKEN),
    },
)
def list_proposal_report_reasons(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[ProposalReportReasonQuestionResponse]]:
    _ = current_user
    return ApiResponse(success=True, data=ProposalReportService.list_reason_questions(db), message="Success")
