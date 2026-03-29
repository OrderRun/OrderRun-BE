"""User profile schemas for extended user information and activity."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

from app.schemas.user import UserResponse
from app.schemas.proposal import ProposalResponse
from app.schemas.offer import OfferResponse


class UserRoles(BaseModel):
    """User roles based on activity."""
    is_orderer: bool = Field(..., alias="isOrderer", description="User has created proposals")
    is_runner: bool = Field(..., alias="isRunner", description="User has submitted offers")

    model_config = {"populate_by_name": True}


class UserProfileResponse(BaseModel):
    """Extended user profile with role information."""
    id: int
    email: str
    nickname: Optional[str] = None
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    status: str
    is_admin: bool = Field(..., alias="isAdmin")
    oauth_provider: str = Field(..., alias="oauthProvider")
    roles: UserRoles
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True, "from_attributes": True}


class OrdererActivitySummary(BaseModel):
    """Summary of user's orderer activity."""
    total_proposals: int = Field(..., alias="totalProposals", description="Total number of proposals created")
    active_proposals: int = Field(..., alias="activeProposals", description="Currently active proposals")
    completed_proposals: int = Field(..., alias="completedProposals", description="Completed proposals (matched)")
    cancelled_proposals: int = Field(..., alias="cancelledProposals", description="Cancelled proposals")
    total_spent: int = Field(..., alias="totalSpent", description="Total errand fees spent")
    recent_proposals: List[ProposalResponse] = Field(..., alias="recentProposals", description="Recent 3 proposals")

    model_config = {"populate_by_name": True}


class RunnerActivitySummary(BaseModel):
    """Summary of user's runner activity."""
    total_offers: int = Field(..., alias="totalOffers", description="Total number of offers submitted")
    waiting_offers: int = Field(..., alias="waitingOffers", description="Offers waiting for response")
    accepted_offers: int = Field(..., alias="acceptedOffers", description="Accepted offers")
    rejected_offers: int = Field(..., alias="rejectedOffers", description="Rejected offers")
    total_earnings: int = Field(..., alias="totalEarnings", description="Total earnings from accepted offers")
    acceptance_rate: float = Field(..., alias="acceptanceRate", description="Offer acceptance rate (0-1)")
    recent_offers: List[OfferResponse] = Field(..., alias="recentOffers", description="Recent 5 offers")

    model_config = {"populate_by_name": True}


class UserActivityResponse(BaseModel):
    """Complete user activity statistics."""
    orderer_activity: OrdererActivitySummary = Field(..., alias="ordererActivity")
    runner_activity: RunnerActivitySummary = Field(..., alias="runnerActivity")

    model_config = {"populate_by_name": True}
