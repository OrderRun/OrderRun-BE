"""Proof schemas for delivery and dispute evidence."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.proof import ProofType


class ProofDeliveryRequest(BaseModel):
    """Runner request to complete delivery."""

    proof_image_url: str | None = Field(None, validation_alias="proofImageUrl")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ProofDisputeRequest(BaseModel):
    """Dispute request."""

    survey_question_id: int = Field(..., validation_alias="surveyQuestionId", ge=1)
    dispute_reason: str = Field(..., validation_alias="disputeReason")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ProofResponse(BaseModel):
    """Proof API response."""

    id: int
    proposal_id: int = Field(..., serialization_alias="proposalId")
    offer_id: int = Field(..., serialization_alias="offerId")
    actor_id: str = Field(..., serialization_alias="actorId")
    proof_type: ProofType = Field(..., serialization_alias="proofType")
    image_url: str | None = Field(None, serialization_alias="imageUrl")
    reason: str | None = None
    survey_question_id: int | None = Field(None, serialization_alias="surveyQuestionId")
    created_at: datetime = Field(..., serialization_alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
