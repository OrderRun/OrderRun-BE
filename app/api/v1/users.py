"""User profile API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.proposal import Proposal, ProposalStatus
from app.models.offer import Offer, OfferStatus
from app.schemas.user_profile import (
    UserProfileResponse,
    UserActivityResponse,
)
from app.schemas.proposal import ProposalResponse
from app.schemas.offer import OfferResponse
from app.services.user_profile_service import UserProfileService


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me/profile", response_model=UserProfileResponse, summary="Get user profile with roles")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current user profile with role information (orderer/runner).

    Returns:
        UserProfileResponse with roles indicating if user has acted as orderer or runner
    """
    service = UserProfileService(db)
    return service.get_user_profile(current_user)


@router.get("/me/activity", response_model=UserActivityResponse, summary="Get user activity statistics")
async def get_user_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get complete user activity statistics including orderer and runner activities.

    This endpoint is designed for the My Page feature.

    Returns:
        UserActivityResponse with detailed statistics for both orderer and runner roles
    """
    service = UserProfileService(db)
    return service.get_user_activity(current_user.id)


@router.get("/me/proposals", response_model=List[ProposalResponse], summary="Get user's proposals")
async def get_user_proposals(
    status: ProposalStatus | None = Query(None, description="Filter by proposal status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get proposals created by the current user (orderer activity).

    Args:
        status: Optional filter by proposal status
        page: Page number (1-indexed)
        limit: Number of items per page (max 100)

    Returns:
        List of ProposalResponse
    """
    query = db.query(Proposal).filter(Proposal.orderer_id == current_user.id)

    if status:
        query = query.filter(Proposal.status == status)

    # Pagination
    offset = (page - 1) * limit
    proposals = query.order_by(Proposal.created_at.desc()).offset(offset).limit(limit).all()

    return [ProposalResponse.model_validate(p) for p in proposals]


@router.get("/me/offers", response_model=List[OfferResponse], summary="Get user's offers")
async def get_user_offers(
    status: OfferStatus | None = Query(None, description="Filter by offer status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get offers submitted by the current user (runner activity).

    Args:
        status: Optional filter by offer status
        page: Page number (1-indexed)
        limit: Number of items per page (max 100)

    Returns:
        List of OfferResponse
    """
    query = db.query(Offer).filter(Offer.runner_id == current_user.id)

    if status:
        query = query.filter(Offer.status == status)

    # Pagination
    offset = (page - 1) * limit
    offers = query.order_by(Offer.created_at.desc()).offset(offset).limit(limit).all()

    return [OfferResponse.model_validate(o) for o in offers]
