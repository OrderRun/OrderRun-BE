"""Offer request and response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.offer import OfferStatus
from app.models.proposal import ProposalStatus


class OfferCreate(BaseModel):
    """Request body for creating an offer."""

    proposal_id: int = Field(..., gt=0, validation_alias="proposalId")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class OfferResponse(BaseModel):
    """Offer API response."""

    id: int
    proposal_id: int = Field(..., serialization_alias="proposalId")
    orderer_id: str = Field(..., serialization_alias="ordererId")
    orderer_name: str = Field(..., serialization_alias="ordererName")
    orderer_level: int = Field(..., serialization_alias="ordererLevel")
    runner_id: str = Field(..., serialization_alias="runnerId")
    runner_name: str = Field(..., serialization_alias="runnerName")
    runner_level: int = Field(..., serialization_alias="runnerLevel")
    status: OfferStatus
    accepted_at: datetime | None = Field(None, serialization_alias="acceptedAt")
    delivery_completed_at: datetime | None = Field(None, serialization_alias="deliveryCompletedAt")
    receipt_confirmed_at: datetime | None = Field(None, serialization_alias="receiptConfirmedAt")
    disputed_at: datetime | None = Field(None, serialization_alias="disputedAt")
    refunded_at: datetime | None = Field(None, serialization_alias="refundedAt")
    created_at: datetime = Field(..., serialization_alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OfferAcceptResponse(BaseModel):
    """Response body for accepted offer orchestration."""

    proposal_id: int = Field(..., serialization_alias="proposalId")
    offer_id: int = Field(..., serialization_alias="offerId")
    proposal_status: ProposalStatus = Field(..., serialization_alias="proposalStatus")
    accepted_offer_status: OfferStatus = Field(..., serialization_alias="acceptedOfferStatus")
    rejected_offer_count: int = Field(..., serialization_alias="rejectedOfferCount")
    orderer_id: str = Field(..., serialization_alias="ordererId")
    orderer_name: str = Field(..., serialization_alias="ordererName")
    orderer_level: int = Field(..., serialization_alias="ordererLevel")
    runner_id: str = Field(..., serialization_alias="runnerId")
    runner_name: str = Field(..., serialization_alias="runnerName")
    runner_level: int = Field(..., serialization_alias="runnerLevel")
    accepted_at: datetime = Field(..., serialization_alias="acceptedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
