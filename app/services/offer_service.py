"""Offer service for business logic."""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus
from app.schemas.offer import OfferCreate, OfferUpdate


class OfferNotFoundError(Exception):
    """Raised when offer is not found."""
    pass


class ProposalNotFoundError(Exception):
    """Raised when proposal is not found."""
    pass


class DuplicateOfferError(Exception):
    """Raised when runner tries to create duplicate offer."""
    pass


class ProposalNotOpenError(Exception):
    """Raised when proposal cannot receive offers."""
    pass


class OfferService:
    """Service for offer-related operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_offer(self, offer_data: OfferCreate) -> Offer:
        """
        Create a new offer.

        Args:
            offer_data: Offer creation data

        Returns:
            Created offer

        Raises:
            ProposalNotFoundError: If proposal doesn't exist
            ProposalNotOpenError: If proposal cannot receive offers
            DuplicateOfferError: If runner already made an offer for this proposal
        """
        # Check if proposal exists
        proposal = self.db.query(Proposal).filter(
            Proposal.id == offer_data.proposal_id
        ).first()

        if not proposal:
            raise ProposalNotFoundError("요청을 찾을 수 없습니다.")

        # Check if proposal can receive offers
        if not proposal.can_receive_offers():
            raise ProposalNotOpenError("제안을 받을 수 없는 요청 상태입니다.")

        # Check for duplicate offer
        existing_offer = self.db.query(Offer).filter(
            Offer.proposal_id == offer_data.proposal_id,
            Offer.runner_id == offer_data.runner_id
        ).first()

        if existing_offer:
            raise DuplicateOfferError("이미 해당 요청에 제안을 제출했습니다.")

        # Create offer
        offer = Offer(
            proposal_id=offer_data.proposal_id,
            runner_id=offer_data.runner_id,
            estimated_time=offer_data.estimated_time,
            message=offer_data.message,
            status=OfferStatus.WAITING
        )

        try:
            self.db.add(offer)

            # Mark proposal as offered if this is the first offer
            if proposal.status == ProposalStatus.POSTED:
                proposal.mark_as_offered()

            self.db.commit()
            self.db.refresh(offer)

            return offer

        except IntegrityError as e:
            self.db.rollback()
            # Handle unique constraint violation
            if "uq_proposal_runner" in str(e):
                raise DuplicateOfferError("이미 해당 요청에 제안을 제출했습니다.")
            raise

    def get_offers_by_proposal(self, proposal_id: int) -> List[Offer]:
        """
        Get all offers for a proposal.

        Args:
            proposal_id: Proposal ID

        Returns:
            List of offers ordered by created_at desc

        Raises:
            ProposalNotFoundError: If proposal doesn't exist
        """
        # Check if proposal exists
        proposal = self.db.query(Proposal).filter(
            Proposal.id == proposal_id
        ).first()

        if not proposal:
            raise ProposalNotFoundError("요청을 찾을 수 없습니다.")

        # Get offers ordered by created_at desc, then id desc (newest first)
        offers = self.db.query(Offer).filter(
            Offer.proposal_id == proposal_id
        ).order_by(Offer.created_at.desc(), Offer.id.desc()).all()

        return offers

    def get_offer(self, offer_id: int) -> Offer:
        """
        Get an offer by ID.

        Args:
            offer_id: Offer ID

        Returns:
            Offer

        Raises:
            OfferNotFoundError: If offer doesn't exist
        """
        offer = self.db.query(Offer).filter(Offer.id == offer_id).first()

        if not offer:
            raise OfferNotFoundError("제안을 찾을 수 없습니다.")

        return offer

    def update_offer(self, offer_id: int, offer_data: OfferUpdate) -> Offer:
        """
        Update an offer.

        Args:
            offer_id: Offer ID
            offer_data: Offer update data

        Returns:
            Updated offer

        Raises:
            OfferNotFoundError: If offer doesn't exist
            ValueError: If offer cannot be modified
        """
        offer = self.get_offer(offer_id)

        if not offer.can_modify():
            raise ValueError("대기 중인 제안만 수정할 수 있습니다.")

        # Update fields
        if offer_data.estimated_time is not None:
            offer.estimated_time = offer_data.estimated_time
        if offer_data.message is not None:
            offer.message = offer_data.message

        self.db.commit()
        self.db.refresh(offer)

        return offer

    def accept_offer(self, offer_id: int) -> Offer:
        """
        Accept an offer.

        Args:
            offer_id: Offer ID

        Returns:
            Accepted offer

        Raises:
            OfferNotFoundError: If offer doesn't exist
            ValueError: If offer cannot be modified
        """
        offer = self.get_offer(offer_id)
        offer.accept()

        self.db.commit()
        self.db.refresh(offer)

        return offer

    def reject_offer(self, offer_id: int) -> Offer:
        """
        Reject an offer.

        Args:
            offer_id: Offer ID

        Returns:
            Rejected offer

        Raises:
            OfferNotFoundError: If offer doesn't exist
            ValueError: If offer cannot be modified
        """
        offer = self.get_offer(offer_id)
        offer.reject()

        self.db.commit()
        self.db.refresh(offer)

        return offer
