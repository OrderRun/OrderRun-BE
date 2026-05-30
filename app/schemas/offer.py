"""Offer request and response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.mission import MissionStatus
from app.models.offer import OfferStatus
from app.models.proposal import ProposalStatus


class OfferCreate(BaseModel):
    """Request body for creating an offer."""

    proposal_id: int = Field(..., gt=0, validation_alias="proposalId")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class OfferAcceptRequest(BaseModel):
    """Request body for accepting an offer and creating a mission."""

    run_fee: int = Field(..., ge=0, validation_alias="runFee")
    item_price: int = Field(..., ge=0, validation_alias="itemPrice")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class OfferResponse(BaseModel):
    """Offer API response."""

    id: int
    proposal_id: int = Field(..., serialization_alias="proposalId")
    runner_id: str = Field(..., serialization_alias="runnerId")
    runner_name: str = Field(..., serialization_alias="runnerName")
    status: OfferStatus
    created_at: datetime = Field(..., serialization_alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OfferAcceptResponse(BaseModel):
    """Response body for accepted offer orchestration."""

    proposal_id: int = Field(..., serialization_alias="proposalId")
    offer_id: int = Field(..., serialization_alias="offerId")
    mission_id: int = Field(..., serialization_alias="missionId")
    proposal_status: ProposalStatus = Field(..., serialization_alias="proposalStatus")
    accepted_offer_status: OfferStatus = Field(..., serialization_alias="acceptedOfferStatus")
    rejected_offer_count: int = Field(..., serialization_alias="rejectedOfferCount")
    mission_status: MissionStatus = Field(..., serialization_alias="missionStatus")
    orderer_id: str = Field(..., serialization_alias="ordererId")
    runner_id: str = Field(..., serialization_alias="runnerId")
    run_fee: int = Field(..., serialization_alias="runFee")
    item_price: int = Field(..., serialization_alias="itemPrice")
    total_amount: int = Field(..., serialization_alias="totalAmount")
    created_at: datetime = Field(..., serialization_alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
