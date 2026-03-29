from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.proposal import Proposal, ProposalStatus
from app.schemas.proposal import ProposalCreate


class ProposalService:
    """Service layer for Proposal business logic."""

    @staticmethod
    def create_proposal(db: Session, proposal_data: ProposalCreate, orderer_id: int) -> Proposal:
        """
        Create a new proposal.

        Args:
            db: Database session
            proposal_data: Proposal creation data
            orderer_id: ID of the user creating the proposal

        Returns:
            Created Proposal instance

        Raises:
            HTTPException: If validation fails
        """
        from datetime import datetime, timezone, timedelta

        # Set payment deadline to 24 hours from now
        now = datetime.now(timezone.utc)
        payment_deadline = now + timedelta(hours=24)

        proposal = Proposal(
            orderer_id=orderer_id,
            title=proposal_data.title,
            content=proposal_data.content,
            deadline=proposal_data.deadline,
            errand_fee=proposal_data.errand_fee,
            status=ProposalStatus.PENDING_PAYMENT,
            payment_status="PENDING",
            payment_deadline=payment_deadline,
        )

        db.add(proposal)
        db.commit()
        db.refresh(proposal)

        return proposal

    @staticmethod
    def get_proposal_by_id(db: Session, proposal_id: int) -> Proposal:
        """
        Get a proposal by ID.

        Args:
            db: Database session
            proposal_id: Proposal ID

        Returns:
            Proposal instance

        Raises:
            HTTPException: If proposal not found
        """
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()

        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "PROPOSAL_NOT_FOUND",
                    "message": "제안을 찾을 수 없습니다.",
                    "details": f"id: {proposal_id}",
                },
            )

        return proposal

    @staticmethod
    def get_all_proposals(db: Session, skip: int = 0, limit: int = 100) -> List[Proposal]:
        """
        Get all proposals.
        Automatically filters out PENDING_PAYMENT status (only visible to orderer/admin).

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Proposal instances
        """
        return (
            db.query(Proposal)
            .filter(Proposal.status != ProposalStatus.PENDING_PAYMENT)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update_proposal_status(db: Session, proposal_id: int, new_status: ProposalStatus) -> Proposal:
        """
        Update proposal status.

        Args:
            db: Database session
            proposal_id: Proposal ID
            new_status: New status

        Returns:
            Updated Proposal instance

        Raises:
            HTTPException: If proposal not found or invalid state transition
        """
        proposal = ProposalService.get_proposal_by_id(db, proposal_id)

        # Validate state transition (can be expanded)
        proposal.status = new_status
        db.commit()
        db.refresh(proposal)

        return proposal

    @staticmethod
    def confirm_payment(
        db: Session, proposal_id: int, admin_id: int, depositor_name: Optional[str] = None
    ) -> Proposal:
        """
        Confirm payment for a proposal and transition to POSTED status.

        Args:
            db: Database session
            proposal_id: Proposal ID
            admin_id: Admin user ID confirming the payment
            depositor_name: Optional depositor name

        Returns:
            Updated Proposal instance

        Raises:
            HTTPException: If proposal not found or invalid state
        """
        proposal = ProposalService.get_proposal_by_id(db, proposal_id)

        # Validate that proposal is in PENDING_PAYMENT status
        if proposal.status != ProposalStatus.PENDING_PAYMENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_STATUS",
                    "message": "입금 대기 상태가 아닙니다.",
                    "details": f"current status: {proposal.status}",
                },
            )

        # Use model method to confirm payment
        try:
            proposal.confirm_payment(admin_id, depositor_name)
            db.commit()
            db.refresh(proposal)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "PAYMENT_CONFIRMATION_FAILED",
                    "message": str(e),
                    "details": None,
                },
            )

        return proposal

    @staticmethod
    def delete_expired_proposals(db: Session) -> int:
        """
        Delete proposals with expired payment deadlines.

        Args:
            db: Database session

        Returns:
            Number of deleted proposals
        """
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        expired_proposals = (
            db.query(Proposal)
            .filter(
                Proposal.status == ProposalStatus.PENDING_PAYMENT,
                Proposal.payment_status == "PENDING",
                Proposal.payment_deadline < now,
            )
            .all()
        )

        count = len(expired_proposals)

        for proposal in expired_proposals:
            db.delete(proposal)

        db.commit()

        return count
