"""Proposal business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import AppError, api_error
from app.events.base import EventBus
from app.events.execution_events import MeetingConfirmedByOrdererEvent
from app.models.offer import Offer, OfferStatus
from app.models.proof import Proof, ProofType
from app.models.proposal import Proposal, ProposalStatus
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.proposal import ProposalDetailResponse, ProposalOwnOfferResponse, ProposalOwnResponse, ProposalRequest


EDITABLE_STATUSES = (ProposalStatus.HOLDING, ProposalStatus.POSTED)
CANCELLABLE_STATUSES = (ProposalStatus.HOLDING, ProposalStatus.POSTED, ProposalStatus.OFFERED)
EXECUTION_OFFER_STATUSES = (
    OfferStatus.ACCEPTED,
    OfferStatus.RUNNER_COMPLETED,
    OfferStatus.ALL_COMPLETED,
    OfferStatus.DISPUTED,
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
    def _get_execution_offer(db: Session, proposal_id: int) -> Offer:
        offer = (
            db.query(Offer)
            .filter(
                Offer.proposal_id == proposal_id,
                Offer.status.in_(EXECUTION_OFFER_STATUSES),
            )
            .order_by(Offer.accepted_at.desc(), Offer.id.desc())
            .first()
        )
        if offer is None:
            raise api_error(AppError.OFFER_NOT_FOUND)
        return offer

    @staticmethod
    def _sync_all_completed(proposal: Proposal, offer: Offer) -> None:
        if proposal.status == ProposalStatus.ORDER_COMPLETED and offer.status == OfferStatus.RUNNER_COMPLETED:
            proposal.mark_all_completed()
            offer.mark_all_completed()

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
    def get_proposal_detail(db: Session, proposal_id: int) -> ProposalDetailResponse:
        proposal = ProposalService._get_proposal(db, proposal_id)
        offers = (
            db.query(Offer)
            .filter(Offer.proposal_id == proposal_id)
            .order_by(Offer.created_at.desc(), Offer.id.desc())
            .all()
        )
        return ProposalDetailResponse(
            id=proposal.id,
            title=proposal.title,
            content=proposal.content,
            deadline=proposal.deadline,
            errand_fee=proposal.errand_fee,
            status=proposal.status,
            matched_at=proposal.matched_at,
            delivery_reported_at=proposal.delivery_reported_at,
            received_confirmed_at=proposal.received_confirmed_at,
            disputed_at=proposal.disputed_at,
            refunded_at=proposal.refunded_at,
            offers=[
                ProposalOwnOfferResponse(
                    id=offer.id,
                    proposal_id=offer.proposal_id,
                    runner_id=offer.runner_id,
                    status=offer.status,
                    created_at=offer.created_at,
                )
                for offer in offers
            ],
        )

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
    def confirm_received(db: Session, proposal_id: int, orderer_id: str) -> ProposalDetailResponse:
        proposal = ProposalService._get_proposal(db, proposal_id)
        ProposalService._ensure_owner(proposal, orderer_id)
        offer = ProposalService._get_execution_offer(db, proposal.id)

        if not proposal.can_confirm_receipt() or not offer.can_confirm_receipt():
            raise api_error(AppError.PROPOSAL_NOT_UPDATABLE, f"status: {proposal.status.value}")

        proposal.confirm_receipt()
        offer.confirm_receipt()
        ProposalService._sync_all_completed(proposal, offer)
        db.flush()
        EventBus.publish(MeetingConfirmedByOrdererEvent(
            offer_id=offer.id,
            proposal_id=proposal.id,
            orderer_id=proposal.orderer_id,
            runner_id=offer.runner_id,
            proposal_title=proposal.title,
        ), db)
        db.commit()
        db.refresh(proposal)
        return ProposalService.get_proposal_detail(db, proposal.id)

    @staticmethod
    def raise_dispute(
        db: Session,
        proposal_id: int,
        orderer_id: str,
        dispute_reason: str,
    ) -> ProposalDetailResponse:
        proposal = ProposalService._get_proposal(db, proposal_id)
        ProposalService._ensure_owner(proposal, orderer_id)
        offer = ProposalService._get_execution_offer(db, proposal.id)

        if not proposal.can_raise_dispute() or not offer.can_raise_dispute():
            raise api_error(AppError.PROPOSAL_NOT_UPDATABLE, f"status: {proposal.status.value}")

        proposal.raise_dispute()
        offer.raise_dispute()
        db.add(Proof(
            proposal_id=proposal.id,
            offer_id=offer.id,
            actor_id=orderer_id,
            proof_type=ProofType.DISPUTE,
            reason=dispute_reason,
        ))
        db.commit()
        db.refresh(proposal)
        return ProposalService.get_proposal_detail(db, proposal.id)

    @staticmethod
    def delete_expired_proposals(db: Session) -> int:
        """Payment expiry cleanup is outside the current Proposal API scope."""

        return 0
