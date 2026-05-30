"""Proposal request and response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.offer import OfferStatus
from app.models.proposal import ProposalStatus


class ProposalRequest(BaseModel):
    """Request body for Proposal create/update APIs."""

    title: str = Field(..., max_length=50)
    content: str = Field(..., max_length=500)
    deadline: str
    errand_fee: int = Field(..., validation_alias="errandFee")

    @field_validator("title", "content")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ProposalResponse(BaseModel):
    """Public Proposal response."""

    id: int
    title: str
    content: str
    deadline: datetime
    errand_fee: int = Field(..., serialization_alias="errandFee")
    status: ProposalStatus

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProposalDetailResponse(ProposalResponse):
    """Proposal detail response."""


class ProposalOwnOfferResponse(BaseModel):
    """Offer summary embedded in own Proposal responses."""

    id: int
    proposal_id: int = Field(..., serialization_alias="proposalId")
    runner_id: str = Field(..., serialization_alias="runnerId")
    status: OfferStatus
    created_at: datetime = Field(..., serialization_alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProposalOwnResponse(ProposalResponse):
    """Proposal response for the orderer including offer summaries."""

    orderer_id: str = Field(..., serialization_alias="ordererId")
    offer_count: int = Field(..., serialization_alias="offerCount")
    offers: list[ProposalOwnOfferResponse]
    created_at: datetime = Field(..., serialization_alias="createdAt")
    updated_at: datetime = Field(..., serialization_alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
