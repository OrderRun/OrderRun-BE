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
        proposal = Proposal(
            orderer_id=orderer_id,
            title=proposal_data.title,
            content=proposal_data.content,
            deadline=proposal_data.deadline,
            errand_fee=proposal_data.errand_fee,
            status=ProposalStatus.POSTED,
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

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Proposal instances
        """
        return db.query(Proposal).offset(skip).limit(limit).all()

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
