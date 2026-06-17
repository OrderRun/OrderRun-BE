"""Offer business logic."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError, api_error
from app.events.base import EventBus
from app.events.offer_events import OfferAcceptedEvent, OfferCreatedEvent
from app.events.execution_events import MeetingConfirmedByRunnerEvent
from app.models.offer import Offer, OfferStatus
from app.models.proof import Proof, ProofType
from app.models.proposal import Proposal, ProposalStatus
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.offer import OfferAcceptResponse, OfferCreate, OfferDetailResponse, OfferResponse, OfferSummaryResponse


OPEN_PROPOSAL_STATUSES = (ProposalStatus.POSTED, ProposalStatus.OFFERED)
ACTIVE_OFFER_STATUSES = (
    OfferStatus.ACCEPTED,
    OfferStatus.RUNNER_COMPLETED,
    OfferStatus.ALL_COMPLETED,
    OfferStatus.DISPUTED,
)
OPEN_CHAT_OFFER_STATUSES = (
    OfferStatus.ACCEPTED,
    OfferStatus.RUNNER_COMPLETED,
    OfferStatus.ALL_COMPLETED,
    OfferStatus.DISPUTED,
    OfferStatus.REFUNDED,
)


class OfferService:
    """Service layer for Offer commands and queries."""

    @staticmethod
    def _get_proposal(db: Session, proposal_id: int) -> Proposal:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if proposal is None:
            raise api_error(AppError.OFFER_PROPOSAL_NOT_FOUND)
        return proposal

    @staticmethod
    def _ensure_proposal_exists(db: Session, proposal_id: int) -> None:
        OfferService._get_proposal(db, proposal_id)

    @staticmethod
    def _get_offer(db: Session, offer_id: int) -> Offer:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if offer is None:
            raise api_error(AppError.OFFER_NOT_FOUND)
        return offer

    @staticmethod
    def _user_profile(db: Session, user_id: str) -> tuple[str, int]:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            return "", 0
        return user.name, user.level

    @staticmethod
    def _response_fields(db: Session, offer: Offer) -> dict:
        proposal = OfferService._get_proposal(db, offer.proposal_id)
        orderer_name, orderer_level = OfferService._user_profile(db, proposal.orderer_id)
        runner_name, runner_level = OfferService._user_profile(db, offer.runner_id)
        return {
            "id": offer.id,
            "proposal_id": offer.proposal_id,
            "orderer_id": proposal.orderer_id,
            "orderer_name": orderer_name,
            "orderer_level": orderer_level,
            "runner_id": offer.runner_id,
            "runner_name": runner_name,
            "runner_level": runner_level,
            "status": offer.status,
            "accepted_at": offer.accepted_at,
            "delivery_completed_at": offer.delivery_completed_at,
            "receipt_confirmed_at": offer.receipt_confirmed_at,
            "disputed_at": offer.disputed_at,
            "refunded_at": offer.refunded_at,
            "created_at": offer.created_at,
        }

    @staticmethod
    def _to_response(db: Session, offer: Offer) -> OfferResponse:
        return OfferResponse(**OfferService._response_fields(db, offer))

    @staticmethod
    def _to_summary_response(db: Session, offer: Offer) -> OfferSummaryResponse:
        return OfferSummaryResponse(**OfferService._response_fields(db, offer))

    @staticmethod
    def _to_detail_response(db: Session, offer: Offer, viewer_id: str) -> OfferDetailResponse:
        fields = OfferService._response_fields(db, offer)
        open_chat_url = None
        if (
            offer.status in OPEN_CHAT_OFFER_STATUSES
            and viewer_id in {fields["orderer_id"], offer.runner_id}
        ):
            open_chat_url = offer.open_chat_url
        return OfferDetailResponse(**fields, open_chat_url=open_chat_url)

    @staticmethod
    def _sync_all_completed(db: Session, offer: Offer, proposal: Proposal) -> None:
        if offer.status == OfferStatus.RUNNER_COMPLETED and proposal.status == ProposalStatus.ORDER_COMPLETED:
            offer.mark_all_completed()
            proposal.mark_all_completed()
            db.query(User).filter(User.id == offer.runner_id).update(
                {User.level: User.level + 1},
                synchronize_session=False,
            )

    @staticmethod
    def create(db: Session, request: OfferCreate, runner_id: str) -> OfferResponse:
        proposal = OfferService._get_proposal(db, request.proposal_id)

        if proposal.orderer_id == runner_id:
            raise api_error(AppError.SELF_OFFER_NOT_ALLOWED)

        if proposal.status not in OPEN_PROPOSAL_STATUSES:
            raise api_error(AppError.PROPOSAL_NOT_OPEN)

        duplicate = (
            db.query(Offer)
            .filter(Offer.proposal_id == request.proposal_id, Offer.runner_id == runner_id)
            .first()
        )
        if duplicate is not None:
            raise api_error(AppError.DUPLICATE_OFFER)

        offer = Offer(proposal_id=request.proposal_id, runner_id=runner_id, status=OfferStatus.WAITING)
        try:
            db.add(offer)
            if proposal.status == ProposalStatus.POSTED:
                proposal.mark_as_offered()
            db.flush()
            EventBus.publish(OfferCreatedEvent(
                offer_id=offer.id,
                proposal_id=proposal.id,
                runner_id=runner_id,
                orderer_id=proposal.orderer_id,
                proposal_title=proposal.title,
            ), db)
            db.commit()
            db.refresh(offer)
        except IntegrityError as exc:
            db.rollback()
            if "uk_proposal_runner" in str(exc) or "uq_proposal_runner" in str(exc):
                raise api_error(AppError.DUPLICATE_OFFER) from exc
            raise

        return OfferService._to_response(db, offer)

    @staticmethod
    def find_offers_by_proposal(
        db: Session,
        proposal_id: int,
        offer_statuses: list[OfferStatus] | None,
    ) -> list[OfferSummaryResponse]:
        OfferService._ensure_proposal_exists(db, proposal_id)
        query = db.query(Offer).filter(Offer.proposal_id == proposal_id)
        if offer_statuses:
            query = query.filter(Offer.status.in_(offer_statuses))

        offers = query.order_by(Offer.created_at.desc(), Offer.id.desc()).all()
        return [OfferService._to_summary_response(db, offer) for offer in offers]

    @staticmethod
    def get_offer_detail(db: Session, offer_id: int, viewer_id: str) -> OfferDetailResponse:
        offer = OfferService._get_offer(db, offer_id)
        return OfferService._to_detail_response(db, offer, viewer_id)

    @staticmethod
    def search_runner_offers(
        db: Session,
        runner_id: str,
        offer_statuses: list[OfferStatus] | None,
        page: int,
        size: int,
    ) -> PageResponse[OfferResponse]:
        query = db.query(Offer).filter(Offer.runner_id == runner_id)
        if offer_statuses:
            query = query.filter(Offer.status.in_(offer_statuses))

        total = query.count()
        offers = (
            query.order_by(Offer.created_at.desc(), Offer.id.desc())
            .offset(page * size)
            .limit(size)
            .all()
        )
        return PageResponse.of(
            content=[OfferService._to_response(db, offer) for offer in offers],
            page_number=page,
            page_size=size,
            total_elements=total,
        )

    @staticmethod
    def cancel(db: Session, offer_id: int, runner_id: str) -> None:
        offer = OfferService._get_offer(db, offer_id)
        if offer.runner_id != runner_id:
            raise api_error(AppError.FORBIDDEN)
        if offer.status != OfferStatus.WAITING:
            raise api_error(AppError.OFFER_NOT_CANCELLABLE)

        offer.cancel()
        db.commit()

    @staticmethod
    def accept(db: Session, offer_id: int, orderer_id: str) -> OfferAcceptResponse:
        offer = OfferService._get_offer(db, offer_id)
        proposal = OfferService._get_proposal(db, offer.proposal_id)

        if proposal.orderer_id != orderer_id:
            raise api_error(AppError.FORBIDDEN)

        if offer.status != OfferStatus.WAITING:
            raise api_error(AppError.OFFER_NOT_ACCEPTABLE)

        existing_active_offer = (
            db.query(Offer)
            .filter(
                Offer.proposal_id == proposal.id,
                Offer.id != offer.id,
                Offer.status.in_(ACTIVE_OFFER_STATUSES),
            )
            .first()
        )
        if existing_active_offer is not None:
            raise api_error(AppError.PROPOSAL_NOT_MATCHABLE)

        if proposal.status != ProposalStatus.OFFERED:
            raise api_error(AppError.PROPOSAL_NOT_MATCHABLE)

        rejected_runner_ids = tuple(
            row[0] for row in db.query(Offer.runner_id).filter(
                Offer.proposal_id == proposal.id,
                Offer.id != offer.id,
                Offer.status == OfferStatus.WAITING,
            ).all()
        )

        offer.accept()
        proposal.status = ProposalStatus.MATCHED
        proposal.matched_at = offer.accepted_at
        rejected_count = (
            db.query(Offer)
            .filter(
                Offer.proposal_id == proposal.id,
                Offer.id != offer.id,
                Offer.status == OfferStatus.WAITING,
            )
            .update({Offer.status: OfferStatus.REJECTED}, synchronize_session=False)
        )
        db.flush()
        EventBus.publish(OfferAcceptedEvent(
            offer_id=offer.id,
            proposal_id=proposal.id,
            accepted_runner_id=offer.runner_id,
            rejected_runner_ids=rejected_runner_ids,
            orderer_id=proposal.orderer_id,
            proposal_title=proposal.title,
        ), db)
        db.commit()
        db.refresh(offer)
        db.refresh(proposal)
        orderer_name, orderer_level = OfferService._user_profile(db, proposal.orderer_id)
        runner_name, runner_level = OfferService._user_profile(db, offer.runner_id)

        return OfferAcceptResponse(
            proposal_id=proposal.id,
            offer_id=offer.id,
            proposal_status=proposal.status,
            accepted_offer_status=offer.status,
            rejected_offer_count=rejected_count,
            orderer_id=proposal.orderer_id,
            orderer_name=orderer_name,
            orderer_level=orderer_level,
            runner_id=offer.runner_id,
            runner_name=runner_name,
            runner_level=runner_level,
            accepted_at=offer.accepted_at,
        )

    @staticmethod
    def complete_delivery(
        db: Session,
        offer_id: int,
        runner_id: str,
        proof_image_url: str | None,
    ) -> OfferResponse:
        offer = OfferService._get_offer(db, offer_id)
        if offer.runner_id != runner_id:
            raise api_error(AppError.FORBIDDEN)

        proposal = OfferService._get_proposal(db, offer.proposal_id)
        if not offer.can_complete_delivery() or proposal.status not in {
            ProposalStatus.MATCHED,
            ProposalStatus.ORDER_COMPLETED,
        }:
            raise api_error(AppError.OFFER_NOT_UPDATABLE, f"status: {offer.status.value}")

        offer.complete_delivery()
        if proposal.status in {ProposalStatus.MATCHED, ProposalStatus.ORDER_COMPLETED}:
            proposal.report_delivery()
        OfferService._sync_all_completed(db, offer, proposal)
        db.add(Proof(
            proposal_id=proposal.id,
            offer_id=offer.id,
            actor_id=runner_id,
            proof_type=ProofType.DELIVERY,
            image_url=proof_image_url,
        ))
        db.flush()
        EventBus.publish(MeetingConfirmedByRunnerEvent(
            offer_id=offer.id,
            proposal_id=proposal.id,
            runner_id=offer.runner_id,
            orderer_id=proposal.orderer_id,
            proposal_title=proposal.title,
        ), db)
        db.commit()
        db.refresh(offer)
        return OfferService._to_response(db, offer)

    @staticmethod
    def raise_dispute(
        db: Session,
        offer_id: int,
        runner_id: str,
        dispute_reason: str,
    ) -> OfferResponse:
        offer = OfferService._get_offer(db, offer_id)
        if offer.runner_id != runner_id:
            raise api_error(AppError.FORBIDDEN)

        proposal = OfferService._get_proposal(db, offer.proposal_id)
        if not offer.can_raise_dispute() or not proposal.can_raise_dispute():
            raise api_error(AppError.OFFER_NOT_UPDATABLE, f"status: {offer.status.value}")

        offer.raise_dispute()
        proposal.raise_dispute()
        db.add(Proof(
            proposal_id=proposal.id,
            offer_id=offer.id,
            actor_id=runner_id,
            proof_type=ProofType.DISPUTE,
            reason=dispute_reason,
        ))
        db.commit()
        db.refresh(offer)
        return OfferService._to_response(db, offer)

    @staticmethod
    def refund(db: Session, offer_id: int) -> OfferResponse:
        offer = OfferService._get_offer(db, offer_id)
        proposal = OfferService._get_proposal(db, offer.proposal_id)
        if not offer.can_refund() or not proposal.can_refund():
            raise api_error(AppError.OFFER_NOT_UPDATABLE, f"status: {offer.status.value}")

        offer.refund()
        proposal.refund()
        db.commit()
        db.refresh(offer)
        return OfferService._to_response(db, offer)
