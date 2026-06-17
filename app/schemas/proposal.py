"""Proposal request and response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from app.models.offer import OfferStatus
from app.models.proposal import ProposalStatus


class ProposalRequest(BaseModel):
    """Request body for Proposal create/update APIs."""

    title: str = Field(..., max_length=50)
    content: str = Field(..., max_length=500)
    deadline: datetime
    errand_fee: int = Field(..., validation_alias="errandFee")

    @field_validator("title", "content")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("deadline")
    @classmethod
    def validate_deadline_has_offset(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise PydanticCustomError("invalid_datetime_offset", "deadline must include timezone offset")
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


class ProposalDetailResponse(BaseModel):
    """Proposal detail response."""

    id: int
    title: str
    content: str
    deadline: datetime
    errand_fee: int = Field(..., serialization_alias="errandFee")
    orderer_id: str = Field(..., serialization_alias="ordererId")
    orderer_name: str = Field(..., serialization_alias="ordererName")
    orderer_level: int = Field(..., serialization_alias="ordererLevel")
    status: ProposalStatus
    matched_at: datetime | None = Field(None, serialization_alias="matchedAt")
    delivery_reported_at: datetime | None = Field(None, serialization_alias="deliveryReportedAt")
    received_confirmed_at: datetime | None = Field(None, serialization_alias="receivedConfirmedAt")
    disputed_at: datetime | None = Field(None, serialization_alias="disputedAt")
    refunded_at: datetime | None = Field(None, serialization_alias="refundedAt")
    open_chat_url: str | None = Field(None, serialization_alias="openChatUrl")
    offers: list[ProposalOwnOfferResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProposalOwnOfferResponse(BaseModel):
    """Offer summary embedded in own Proposal responses."""

    id: int
    proposal_id: int = Field(..., serialization_alias="proposalId")
    runner_id: str = Field(..., serialization_alias="runnerId")
    runner_name: str = Field(..., serialization_alias="runnerName")
    runner_level: int = Field(..., serialization_alias="runnerLevel")
    status: OfferStatus
    created_at: datetime = Field(..., serialization_alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProposalOwnResponse(BaseModel):
    """Proposal response for the orderer including offer summaries."""

    id: int
    orderer_id: str = Field(..., serialization_alias="ordererId")
    orderer_name: str = Field(..., serialization_alias="ordererName")
    orderer_level: int = Field(..., serialization_alias="ordererLevel")
    title: str
    content: str
    deadline: datetime
    errand_fee: int = Field(..., serialization_alias="errandFee")
    status: ProposalStatus
    offer_count: int = Field(..., serialization_alias="offerCount")
    offers: list[ProposalOwnOfferResponse]
    created_at: datetime = Field(..., serialization_alias="createdAt")
    updated_at: datetime = Field(..., serialization_alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
