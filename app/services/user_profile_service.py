"""User profile service for retrieving user roles and activity statistics."""
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Tuple

from app.models.user import User
from app.models.proposal import Proposal, ProposalStatus
from app.models.offer import Offer, OfferStatus
from app.schemas.user_profile import (
    UserRoles,
    UserProfileResponse,
    OrdererActivitySummary,
    RunnerActivitySummary,
    UserActivityResponse,
)
from app.schemas.proposal import ProposalResponse
from app.schemas.offer import OfferResponse


class UserProfileService:
    """Service for user profile and activity operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_roles(self, user_id: int) -> UserRoles:
        """
        Determine user roles based on their activity.

        Args:
            user_id: User ID

        Returns:
            UserRoles with is_orderer and is_runner flags
        """
        # Check if user has created any proposals
        has_proposals = (
            self.db.query(Proposal)
            .filter(Proposal.orderer_id == user_id)
            .limit(1)
            .first()
        ) is not None

        # Check if user has submitted any offers
        has_offers = (
            self.db.query(Offer)
            .filter(Offer.runner_id == user_id)
            .limit(1)
            .first()
        ) is not None

        return UserRoles(
            is_orderer=has_proposals,
            is_runner=has_offers
        )

    def get_user_profile(self, user: User) -> UserProfileResponse:
        """
        Get user profile with role information.

        Args:
            user: User object

        Returns:
            UserProfileResponse with roles
        """
        roles = self.get_user_roles(user.id)

        return UserProfileResponse(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            phone_number=user.phone_number,
            status=user.status.value,
            is_admin=user.is_admin,
            oauth_provider=user.oauth_provider.value,
            roles=roles,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def get_orderer_activity(self, user_id: int) -> OrdererActivitySummary:
        """
        Get orderer activity statistics.

        Args:
            user_id: User ID

        Returns:
            OrdererActivitySummary with statistics
        """
        # Count proposals by status
        status_counts = (
            self.db.query(
                Proposal.status,
                func.count(Proposal.id).label("count"),
            )
            .filter(Proposal.orderer_id == user_id)
            .group_by(Proposal.status)
            .all()
        )

        # Convert to dict
        status_dict = {status: count for status, count in status_counts}

        # Calculate statistics
        total_proposals = sum(status_dict.values())
        active_proposals = status_dict.get(ProposalStatus.POSTED, 0) + status_dict.get(ProposalStatus.OFFERED, 0)
        completed_proposals = status_dict.get(ProposalStatus.MATCHED, 0)
        cancelled_proposals = status_dict.get(ProposalStatus.CANCELLED, 0)

        # Calculate total spent (only for matched proposals)
        total_spent = (
            self.db.query(func.coalesce(func.sum(Proposal.errand_fee), 0))
            .filter(
                Proposal.orderer_id == user_id,
                Proposal.status == ProposalStatus.MATCHED,
            )
            .scalar()
        )

        # Get recent proposals (latest 3)
        recent_proposals_db = (
            self.db.query(Proposal)
            .filter(Proposal.orderer_id == user_id)
            .order_by(Proposal.created_at.desc())
            .limit(3)
            .all()
        )

        recent_proposals = [
            ProposalResponse.model_validate(p) for p in recent_proposals_db
        ]

        return OrdererActivitySummary(
            total_proposals=total_proposals,
            active_proposals=active_proposals,
            completed_proposals=completed_proposals,
            cancelled_proposals=cancelled_proposals,
            total_spent=int(total_spent) if total_spent else 0,
            recent_proposals=recent_proposals,
        )

    def get_runner_activity(self, user_id: int) -> RunnerActivitySummary:
        """
        Get runner activity statistics.

        Args:
            user_id: User ID

        Returns:
            RunnerActivitySummary with statistics
        """
        # Count offers by status
        status_counts = (
            self.db.query(
                Offer.status,
                func.count(Offer.id).label("count"),
            )
            .filter(Offer.runner_id == user_id)
            .group_by(Offer.status)
            .all()
        )

        # Convert to dict
        status_dict = {status: count for status, count in status_counts}

        # Calculate statistics
        total_offers = sum(status_dict.values())
        waiting_offers = status_dict.get(OfferStatus.WAITING, 0)
        accepted_offers = status_dict.get(OfferStatus.ACCEPTED, 0)
        rejected_offers = status_dict.get(OfferStatus.REJECTED, 0)

        # Calculate acceptance rate (accepted / (accepted + rejected))
        responded_offers = accepted_offers + rejected_offers
        acceptance_rate = accepted_offers / responded_offers if responded_offers > 0 else 0.0

        # Calculate total earnings (sum of errand_fee for accepted offers)
        total_earnings = (
            self.db.query(func.coalesce(func.sum(Proposal.errand_fee), 0))
            .join(Offer, Offer.proposal_id == Proposal.id)
            .filter(
                Offer.runner_id == user_id,
                Offer.status == OfferStatus.ACCEPTED,
            )
            .scalar()
        )

        # Get recent offers (latest 5)
        recent_offers_db = (
            self.db.query(Offer)
            .filter(Offer.runner_id == user_id)
            .order_by(Offer.created_at.desc())
            .limit(5)
            .all()
        )

        recent_offers = [
            OfferResponse.model_validate(o) for o in recent_offers_db
        ]

        return RunnerActivitySummary(
            total_offers=total_offers,
            waiting_offers=waiting_offers,
            accepted_offers=accepted_offers,
            rejected_offers=rejected_offers,
            total_earnings=int(total_earnings) if total_earnings else 0,
            acceptance_rate=round(acceptance_rate, 2),
            recent_offers=recent_offers,
        )

    def get_user_activity(self, user_id: int) -> UserActivityResponse:
        """
        Get complete user activity statistics.

        Args:
            user_id: User ID

        Returns:
            UserActivityResponse with orderer and runner activities
        """
        orderer_activity = self.get_orderer_activity(user_id)
        runner_activity = self.get_runner_activity(user_id)

        return UserActivityResponse(
            orderer_activity=orderer_activity,
            runner_activity=runner_activity,
        )
