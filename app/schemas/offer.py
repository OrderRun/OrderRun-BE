"""Offer schemas for request/response validation."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

from app.models.offer import OfferStatus


class OfferCreate(BaseModel):
    """Schema for creating a new offer."""
    proposal_id: int = Field(..., gt=0, description="Proposal ID")
    runner_id: int = Field(..., gt=0, description="Runner user ID")
    estimated_time: int = Field(..., ge=1, description="Estimated time in minutes")
    message: Optional[str] = Field(None, max_length=500, description="Offer message")

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if v is not None and len(v) > 500:
            raise ValueError('Message must not exceed 500 characters')
        return v


class OfferUpdate(BaseModel):
    """Schema for updating an offer."""
    estimated_time: Optional[int] = Field(None, ge=1, description="Estimated time in minutes")
    message: Optional[str] = Field(None, max_length=500, description="Offer message")

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if v is not None and len(v) > 500:
            raise ValueError('Message must not exceed 500 characters')
        return v


class OfferResponse(BaseModel):
    """Schema for offer response."""
    id: int
    proposal_id: int = Field(..., alias="proposalId")
    runner_id: int = Field(..., alias="runnerId")
    estimated_time: int = Field(..., alias="estimatedTime")
    message: Optional[str] = None
    status: OfferStatus
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class ApiResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = True
    data: Optional[dict] = None
    message: str = "Success"


class ErrorDetail(BaseModel):
    """Error detail schema."""
    code: str
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""
    success: bool = False
    error: ErrorDetail
    timestamp: datetime
