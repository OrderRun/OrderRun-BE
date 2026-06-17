"""Dispute survey API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.dispute_survey import DisputeSurveyTargetType


class DisputeSurveyQuestionResponse(BaseModel):
    """Question shown to the client before dispute submission."""

    id: int = Field(..., description="질문 ID")
    target_type: DisputeSurveyTargetType = Field(..., serialization_alias="targetType", description="질문 대상")
    question_text: str = Field(..., serialization_alias="questionText", description="질문 내용")
    display_order: int = Field(..., serialization_alias="displayOrder", description="클라이언트 표시 순서")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
