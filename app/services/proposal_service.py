"""Proposal business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import AppError, api_error
from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.proposal import ProposalOwnOfferResponse, ProposalOwnResponse, ProposalRequest


EDITABLE_STATUSES = (ProposalStatus.HOLDING, ProposalStatus.POSTED)
CANCELLABLE_STATUSES = (ProposalStatus.HOLDING, ProposalStatus.POSTED, ProposalStatus.OFFERED)
DETAIL_VISIBLE_STATUSES = (
    ProposalStatus.POSTED,
    ProposalStatus.OFFERED,
    ProposalStatus.MATCHED,
    ProposalStatus.CANCELLED,
)


class ProposalService:
    """Service layer for Proposal commands and queries."""

    @staticmethod
    def _get_existing_user(db: Session, user_id: str) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise api_error(AppError.USER_NOT_FOUND)
        return user

    @staticmethod
    def _get_proposal(db: Session, proposal_id: int) -> Proposal:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if proposal is None:
            raise api_error(AppError.PROPOSAL_NOT_FOUND, f"id: {proposal_id}")
        return proposal

    @staticmethod
    def _ensure_owner(proposal: Proposal, user_id: str) -> None:
        if proposal.orderer_id != user_id:
            raise api_error(AppError.FORBIDDEN)

    @staticmethod
    def search_proposals(
        db: Session,
        proposal_statuses: list[ProposalStatus] | None,
        page: int,
        size: int,
    ) -> PageResponse[Proposal]:
        query = db.query(Proposal)
        if proposal_statuses:
            query = query.filter(Proposal.status.in_(proposal_statuses))
        total = query.count()
        items = (
            query.order_by(Proposal.created_at.desc(), Proposal.id.desc())
            .offset(page * size)
            .limit(size)
            .all()
        )
        return PageResponse.of(content=items, page_number=page, page_size=size, total_elements=total)

    @staticmethod
    def get_proposal_detail(db: Session, proposal_id: int) -> Proposal:
        proposal = ProposalService._get_proposal(db, proposal_id)
        if proposal.status not in DETAIL_VISIBLE_STATUSES:
            raise api_error(AppError.PROPOSAL_NOT_FOUND, f"id: {proposal_id}")
        return proposal

    @staticmethod
    def search_owner_proposals(
        db: Session,
        user_id: str,
        proposal_statuses: list[ProposalStatus] | None,
        page: int,
        size: int,
    ) -> PageResponse[ProposalOwnResponse]:
        query = db.query(Proposal).filter(Proposal.orderer_id == user_id)
        if proposal_statuses:
            query = query.filter(Proposal.status.in_(proposal_statuses))

        total = query.count()
        proposals = (
            query.order_by(Proposal.created_at.desc(), Proposal.id.desc())
            .offset(page * size)
            .limit(size)
            .all()
        )
        proposal_ids = [proposal.id for proposal in proposals]
        offers_by_proposal: dict[int, list[Offer]] = {proposal_id: [] for proposal_id in proposal_ids}

        if proposal_ids:
            offers = (
                db.query(Offer)
                .filter(Offer.proposal_id.in_(proposal_ids))
                .order_by(Offer.created_at.desc(), Offer.id.desc())
                .all()
            )
            for offer in offers:
                offers_by_proposal.setdefault(offer.proposal_id, []).append(offer)

        items = [
            ProposalOwnResponse(
                id=proposal.id,
                orderer_id=proposal.orderer_id,
                title=proposal.title,
                content=proposal.content,
                deadline=proposal.deadline,
                errand_fee=proposal.errand_fee,
                status=proposal.status,
                offer_count=len(offers_by_proposal.get(proposal.id, [])),
                offers=[
                    ProposalOwnOfferResponse(
                        id=offer.id,
                        proposal_id=offer.proposal_id,
                        runner_id=offer.runner_id,
                        status=offer.status,
                        created_at=offer.created_at,
                    )
                    for offer in offers_by_proposal.get(proposal.id, [])
                ],
                created_at=proposal.created_at,
                updated_at=proposal.updated_at,
            )
            for proposal in proposals
        ]
        return PageResponse.of(content=items, page_number=page, page_size=size, total_elements=total)

    @staticmethod
    def create(db: Session, request: ProposalRequest, orderer_id: str) -> Proposal:
        ProposalService._get_existing_user(db, orderer_id)
        proposal = Proposal.create_proposal(
            orderer_id=orderer_id,
            title=request.title,
            content=request.content,
            deadline=request.deadline,
            errand_fee=request.errand_fee,
        )
        db.add(proposal)
        db.commit()
        db.refresh(proposal)
        return proposal

    @staticmethod
    def update(db: Session, proposal_id: int, request: ProposalRequest, orderer_id: str) -> Proposal:
        proposal = ProposalService._get_proposal(db, proposal_id)
        ProposalService._ensure_owner(proposal, orderer_id)
        if proposal.status not in EDITABLE_STATUSES:
            raise api_error(AppError.PROPOSAL_NOT_EDITABLE, f"status: {proposal.status.value}")

        proposal.update_proposal(
            title=request.title,
            content=request.content,
            deadline=request.deadline,
            errand_fee=request.errand_fee,
        )
        db.commit()
        db.refresh(proposal)
        return proposal

    @staticmethod
    def cancel(db: Session, proposal_id: int, orderer_id: str) -> Proposal:
        proposal = ProposalService._get_proposal(db, proposal_id)
        ProposalService._ensure_owner(proposal, orderer_id)
        if proposal.status not in CANCELLABLE_STATUSES:
            raise api_error(AppError.PROPOSAL_NOT_CANCELLABLE, f"status: {proposal.status.value}")

        should_reject_waiting_offers = proposal.status == ProposalStatus.OFFERED
        proposal.status = ProposalStatus.CANCELLED
        if should_reject_waiting_offers:
            (
                db.query(Offer)
                .filter(Offer.proposal_id == proposal.id, Offer.status == OfferStatus.WAITING)
                .update({Offer.status: OfferStatus.REJECTED}, synchronize_session=False)
            )

        db.commit()
        db.refresh(proposal)
        return proposal

    @staticmethod
    def confirm_payment(db: Session, proposal_id: int) -> Proposal:
        proposal = ProposalService._get_proposal(db, proposal_id)
        if proposal.status != ProposalStatus.HOLDING:
            raise api_error(AppError.INVALID_STATUS, f"current status: {proposal.status.value}")
        proposal.status = ProposalStatus.POSTED
        db.commit()
        db.refresh(proposal)
        return proposal

    @staticmethod
    def delete_expired_proposals(db: Session) -> int:
        """Payment expiry cleanup is outside the current Proposal API scope."""

        return 0
