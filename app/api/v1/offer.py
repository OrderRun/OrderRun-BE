"""Offer API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.schemas.offer import (
    OfferCreate,
    OfferResponse,
    ApiResponse,
    ErrorResponse,
    ErrorDetail
)
from app.services.offer_service import (
    OfferService,
    ProposalNotFoundError,
    ProposalNotOpenError,
    DuplicateOfferError,
    OfferNotFoundError
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


@router.get("", status_code=status.HTTP_200_OK, summary="Get offers by proposal")
async def get_offers(
    proposalId: int = Query(..., description="Proposal ID to get offers for"),
    db: Session = Depends(get_db)
):
    """
    Get all offers for a specific proposal.

    Args:
        proposalId: Proposal ID
        db: Database session

    Returns:
        ApiResponse with list of offers

    Raises:
        404: Proposal not found
    """
    service = OfferService(db)

    try:
        offers = service.get_offers_by_proposal(proposalId)

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
