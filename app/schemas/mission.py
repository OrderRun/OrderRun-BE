"""Mission schemas for API request/response."""
from __future__ import annotations

from datetime import datetime
import enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.mission import MissionStatus


class MissionRole(str, enum.Enum):
    """Role filter for current user's missions."""

    ORDERER = "ORDERER"
    RUNNER = "RUNNER"


class MissionAction(str, enum.Enum):
    """Supported mission update actions."""

    START_PROGRESS = "START_PROGRESS"
    COMPLETE_DELIVERY = "COMPLETE_DELIVERY"
    CONFIRM_RECEIVED = "CONFIRM_RECEIVED"
    DISPUTE = "DISPUTE"


class MissionUserSummary(BaseModel):
    """Nested user summary in mission responses."""

    id: str
    name: str
    phone: Optional[str] = None


class MissionUpdateRequest(BaseModel):
    """Mission status update request."""

    action: MissionAction
    proof_image_url: Optional[str] = Field(None, validation_alias="proofImageUrl")
    dispute_reason: Optional[str] = Field(None, validation_alias="disputeReason")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class MissionResponse(BaseModel):
    """Mission response schema."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int = Field(..., serialization_alias="id")
    proposal_id: int = Field(..., serialization_alias="proposalId")
    offer_id: int = Field(..., serialization_alias="offerId")
    orderer: MissionUserSummary
    runner: MissionUserSummary
    run_fee: int = Field(..., serialization_alias="runFee")
    item_price: int = Field(..., serialization_alias="itemPrice")
    total_amount: int = Field(..., serialization_alias="totalAmount")
    status: MissionStatus = Field(..., serialization_alias="status")
    delivery_proof_image_url: Optional[str] = Field(None, serialization_alias="deliveryProofImageUrl")
    dispute_reason: Optional[str] = Field(None, serialization_alias="disputeReason")
    created_at: datetime = Field(..., serialization_alias="createdAt")
    pickup_at: Optional[datetime] = Field(None, serialization_alias="pickupAt")
    delivery_completed_at: Optional[datetime] = Field(None, serialization_alias="deliveryCompletedAt")
    received_confirmed_at: Optional[datetime] = Field(None, serialization_alias="receivedConfirmedAt")
    settled_at: Optional[datetime] = Field(None, serialization_alias="settledAt")


class DisputeCreate(BaseModel):
    """Dispute creation request schema."""

    reason: str = Field(..., min_length=1, max_length=1000, description="Dispute reason")
