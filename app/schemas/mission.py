"""Mission schemas for API request/response."""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class MissionResponse(BaseModel):
    """Mission response schema."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int = Field(..., serialization_alias="id")
    proposal_id: int = Field(..., serialization_alias="proposalId")
    offer_id: int = Field(..., serialization_alias="offerId")
    orderer_id: str = Field(..., serialization_alias="ordererId")
    runner_id: str = Field(..., serialization_alias="runnerId")
    contract_amount: int = Field(..., serialization_alias="contractAmount")
    run_fee: int = Field(..., serialization_alias="runFee")
    item_price: int = Field(..., serialization_alias="itemPrice")
    total_amount: int = Field(..., serialization_alias="totalAmount")
    status: str = Field(..., serialization_alias="status")
    delivery_proof_image_url: Optional[str] = Field(None, serialization_alias="deliveryProofImageUrl")
    dispute_reason: Optional[str] = Field(None, serialization_alias="disputeReason")
    created_at: datetime = Field(..., serialization_alias="createdAt")
    started_at: Optional[datetime] = Field(None, serialization_alias="startedAt")
    completed_at: Optional[datetime] = Field(None, serialization_alias="completedAt")
    settled_at: Optional[datetime] = Field(None, serialization_alias="settledAt")
    updated_at: datetime = Field(..., serialization_alias="updatedAt")


class DisputeCreate(BaseModel):
    """Dispute creation request schema."""

    reason: str = Field(..., min_length=1, max_length=1000, description="Dispute reason")
