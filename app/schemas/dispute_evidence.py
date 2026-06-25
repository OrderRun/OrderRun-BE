"""Dispute evidence API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DisputeRequest(BaseModel):
    """Dispute request."""

    survey_question_id: int = Field(..., validation_alias="surveyQuestionId", ge=1)
    dispute_reason: str = Field(..., validation_alias="disputeReason")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class DisputeEvidenceResponse(BaseModel):
    """Dispute evidence API response."""

    id: int
    proposal_id: int = Field(..., serialization_alias="proposalId")
    offer_id: int = Field(..., serialization_alias="offerId")
    actor_id: str = Field(..., serialization_alias="actorId")
    reason: str
    survey_question_id: int = Field(..., serialization_alias="surveyQuestionId")
    created_at: datetime = Field(..., serialization_alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
