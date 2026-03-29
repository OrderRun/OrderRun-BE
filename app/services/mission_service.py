"""Mission service for business logic."""
from sqlalchemy.orm import Session
from typing import List

from app.models.mission import Mission, MissionStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.offer import Offer, OfferStatus


class MissionNotFoundError(Exception):
    """Raised when mission is not found."""
    pass


class OfferNotFoundError(Exception):
    """Raised when offer is not found."""
    pass


class ProposalNotFoundError(Exception):
    """Raised when proposal is not found."""
    pass


class UnauthorizedAccessError(Exception):
    """Raised when user tries to access resources they don't own."""
    pass


class InvalidOfferStatusError(Exception):
    """Raised when offer status is not valid for the operation."""
    pass


class InvalidProposalStatusError(Exception):
    """Raised when proposal status is not valid for the operation."""
    pass


class MissionService:
    """Service for mission-related operations."""

    def __init__(self, db: Session):
        self.db = db

    def accept_offer_and_create_mission(self, offer_id: int, orderer_id: int) -> Mission:
        """
        Accept an offer and create a mission.

        This operation:
        1. Validates the offer exists and is in WAITING status
        2. Validates the proposal exists and belongs to the orderer
        3. Creates a mission with contract amount snapshot
        4. Updates offer status to ACCEPTED
        5. Updates proposal status to MATCHED
        6. Rejects all other waiting offers for the same proposal

        Args:
            offer_id: ID of the offer to accept
            orderer_id: ID of the orderer accepting the offer

        Returns:
            Created mission

        Raises:
            OfferNotFoundError: If offer doesn't exist
            InvalidOfferStatusError: If offer is not in WAITING status
            ProposalNotFoundError: If proposal doesn't exist
            UnauthorizedAccessError: If user is not the proposal owner
            InvalidProposalStatusError: If proposal is not in OFFERED status
        """
        # 1. Validate offer
        offer = self.db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer:
            raise OfferNotFoundError("제안을 찾을 수 없습니다.")

        if offer.status != OfferStatus.WAITING:
            raise InvalidOfferStatusError("이미 처리된 제안입니다.")

        # 2. Validate proposal
        proposal = self.db.query(Proposal).filter(
            Proposal.id == offer.proposal_id
        ).first()

        if not proposal:
            raise ProposalNotFoundError("요청을 찾을 수 없습니다.")

        if proposal.orderer_id != orderer_id:
            raise UnauthorizedAccessError("본인의 요청에 대한 제안만 수락할 수 있습니다.")

        if proposal.status != ProposalStatus.OFFERED:
            raise InvalidProposalStatusError("제안을 받을 수 없는 요청 상태입니다.")

        # 3. Create mission with contract amount snapshot
        mission = Mission(
            proposal_id=proposal.id,
            offer_id=offer.id,
            orderer_id=proposal.orderer_id,
            runner_id=offer.runner_id,
            contract_amount=proposal.errand_fee,  # Snapshot of the contract amount
            status=MissionStatus.CREATED
        )

        try:
            self.db.add(mission)

            # 4. Update offer status to ACCEPTED
            offer.status = OfferStatus.ACCEPTED

            # 5. Update proposal status to MATCHED
            proposal.status = ProposalStatus.MATCHED

            # 6. Reject all other waiting offers for the same proposal
            other_offers = self.db.query(Offer).filter(
                Offer.proposal_id == proposal.id,
                Offer.id != offer.id,
                Offer.status == OfferStatus.WAITING
            ).all()

            for other_offer in other_offers:
                other_offer.status = OfferStatus.REJECTED

            self.db.commit()
            self.db.refresh(mission)

            # TODO: Send notifications to accepted and rejected runners
            # - Accepted runner: "Your offer has been accepted"
            # - Rejected runners: "Your offer has been rejected"

            return mission

        except Exception as e:
            self.db.rollback()
            raise

    def get_mission_by_id(self, mission_id: int) -> Mission:
        """
        Get a mission by ID.

        Args:
            mission_id: Mission ID

        Returns:
            Mission

        Raises:
            MissionNotFoundError: If mission doesn't exist
        """
        mission = self.db.query(Mission).filter(Mission.id == mission_id).first()

        if not mission:
            raise MissionNotFoundError("미션을 찾을 수 없습니다.")

        return mission

    def get_missions_by_orderer(self, orderer_id: int, skip: int = 0, limit: int = 100) -> List[Mission]:
        """
        Get all missions for an orderer.

        Args:
            orderer_id: Orderer ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of missions
        """
        missions = self.db.query(Mission).filter(
            Mission.orderer_id == orderer_id
        ).order_by(Mission.created_at.desc()).offset(skip).limit(limit).all()

        return missions

    def get_missions_by_runner(self, runner_id: int, skip: int = 0, limit: int = 100) -> List[Mission]:
        """
        Get all missions for a runner.

        Args:
            runner_id: Runner ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of missions
        """
        missions = self.db.query(Mission).filter(
            Mission.runner_id == runner_id
        ).order_by(Mission.created_at.desc()).offset(skip).limit(limit).all()

        return missions
