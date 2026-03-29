"""Offer API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.offer import (
    OfferCreate,
    OfferResponse,
    ApiResponse,
    ErrorResponse,
    ErrorDetail
)
from app.schemas.mission import MissionResponse
from app.services.offer_service import (
    OfferService,
    ProposalNotFoundError,
    ProposalNotOpenError,
    DuplicateOfferError,
    OfferNotFoundError,
    UnauthorizedAccessError,
    SelfOfferNotAllowedError
)
from app.services.mission_service import (
    MissionService,
    InvalidOfferStatusError,
    InvalidProposalStatusError,
    OfferNotFoundError as MissionOfferNotFoundError,
    ProposalNotFoundError as MissionProposalNotFoundError,
    UnauthorizedAccessError as MissionUnauthorizedAccessError
)

router = APIRouter(prefix="/offer", tags=["Offer"])


def create_error_response(code: str, message: str, details=None) -> dict:
    """Create standardized error response."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new offer")
async def create_offer(
    offer_data: OfferCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new offer for a proposal.

    Args:
        offer_data: Offer creation data
        db: Database session

    Returns:
        ApiResponse with created offer

    Raises:
        400: Validation error
        404: Proposal not found
        409: Duplicate offer or proposal not open
    """
    service = OfferService(db)

    try:
        offer = service.create_offer(offer_data)

        # Convert to response format
        offer_response = OfferResponse.model_validate(offer)

        return {
            "success": True,
            "data": offer_response.model_dump(by_alias=True),
            "message": "제안이 제출되었습니다."
        }

    except ProposalNotFoundError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=create_error_response("PROPOSAL_NOT_FOUND", str(e))
        )

    except SelfOfferNotAllowedError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_error_response("SELF_OFFER_NOT_ALLOWED", str(e))
        )

    except ProposalNotOpenError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=create_error_response("PROPOSAL_NOT_OPEN", str(e))
        )

    except DuplicateOfferError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=create_error_response("DUPLICATE_OFFER", str(e))
        )

    except ValueError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_error_response("VALIDATION_ERROR", str(e))
        )


@router.get("", status_code=status.HTTP_200_OK, summary="Get offers by proposal (orderer only)")
async def get_offers(
    proposalId: int = Query(..., description="Proposal ID to get offers for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all offers for a specific proposal.
    Only the orderer who created the proposal can view offers.

    Args:
        proposalId: Proposal ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ApiResponse with list of offers

    Raises:
        401: Unauthorized (not authenticated)
        403: Forbidden (not the orderer of the proposal)
        404: Proposal not found
    """
    service = OfferService(db)

    try:
        offers = service.get_offers_by_proposal(proposalId, orderer_id=current_user.id)

        # Convert to response format
        offers_response = [
            OfferResponse.model_validate(offer).model_dump(by_alias=True)
            for offer in offers
        ]

        return {
            "success": True,
            "data": offers_response,
            "message": "Success"
        }

    except ProposalNotFoundError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=create_error_response("PROPOSAL_NOT_FOUND", str(e))
        )

    except UnauthorizedAccessError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=create_error_response("FORBIDDEN", str(e))
        )


@router.post("/{offer_id}/accept", status_code=status.HTTP_201_CREATED, summary="Accept an offer and create a mission (orderer only)")
async def accept_offer(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accept an offer and create a mission.

    This endpoint:
    1. Validates the offer and proposal
    2. Creates a mission with contract amount snapshot
    3. Updates the accepted offer to ACCEPTED status
    4. Updates the proposal to MATCHED status
    5. Rejects all other waiting offers for the same proposal

    Only the orderer who created the proposal can accept offers.

    Args:
        offer_id: ID of the offer to accept
        current_user: Current authenticated user (must be orderer)
        db: Database session

    Returns:
        ApiResponse with created mission

    Raises:
        401: Unauthorized (not authenticated)
        403: Forbidden (not the orderer of the proposal)
        404: Offer or proposal not found
        400: Invalid offer or proposal status
    """
    mission_service = MissionService(db)

    try:
        mission = mission_service.accept_offer_and_create_mission(
            offer_id=offer_id,
            orderer_id=current_user.id
        )

        # Convert to response format
        mission_response = MissionResponse.model_validate(mission)

        return {
            "success": True,
            "data": mission_response.model_dump(by_alias=True),
            "message": "제안이 수락되어 미션이 생성되었습니다."
        }

    except (OfferNotFoundError, MissionOfferNotFoundError) as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=create_error_response("OFFER_NOT_FOUND", str(e))
        )

    except (ProposalNotFoundError, MissionProposalNotFoundError) as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=create_error_response("PROPOSAL_NOT_FOUND", str(e))
        )

    except (UnauthorizedAccessError, MissionUnauthorizedAccessError) as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=create_error_response("FORBIDDEN", str(e))
        )

    except InvalidOfferStatusError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_error_response("INVALID_OFFER_STATUS", str(e))
        )

    except InvalidProposalStatusError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_error_response("INVALID_PROPOSAL_STATUS", str(e))
        )
