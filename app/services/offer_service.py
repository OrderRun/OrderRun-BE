"""Offer business logic."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError, api_error
from app.models.mission import Mission, MissionStatus
from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.offer import OfferAcceptRequest, OfferAcceptResponse, OfferCreate, OfferResponse


OPEN_PROPOSAL_STATUSES = (ProposalStatus.POSTED, ProposalStatus.OFFERED)


class OfferService:
    """Service layer for Offer commands and queries."""

    @staticmethod
    def _get_proposal(db: Session, proposal_id: int) -> Proposal:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if proposal is None:
            raise api_error(AppError.OFFER_PROPOSAL_NOT_FOUND)
        return proposal

    @staticmethod
    def _get_offer(db: Session, offer_id: int) -> Offer:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if offer is None:
            raise api_error(AppError.OFFER_NOT_FOUND)
        return offer

    @staticmethod
    def _runner_name(db: Session, runner_id: str) -> str:
        runner = db.query(User).filter(User.id == runner_id).first()
        return runner.name if runner is not None else ""

    @staticmethod
    def _to_response(db: Session, offer: Offer) -> OfferResponse:
        return OfferResponse(
            id=offer.id,
            proposal_id=offer.proposal_id,
            runner_id=offer.runner_id,
            runner_name=OfferService._runner_name(db, offer.runner_id),
            status=offer.status,
            created_at=offer.created_at,
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
            db.commit()
            db.refresh(offer)
        except IntegrityError as exc:
            db.rollback()
            if "uk_proposal_runner" in str(exc) or "uq_proposal_runner" in str(exc):
                raise api_error(AppError.DUPLICATE_OFFER) from exc
            raise

        return OfferService._to_response(db, offer)

    @staticmethod
    def list_by_proposal(db: Session, proposal_id: int, user_id: str) -> list[OfferResponse]:
        OfferService._get_proposal(db, proposal_id)
        offers = (
            db.query(Offer)
            .filter(Offer.proposal_id == proposal_id)
            .order_by(Offer.created_at.desc(), Offer.id.desc())
            .all()
        )
        return [OfferService._to_response(db, offer) for offer in offers]

    @staticmethod
    def get_detail(db: Session, offer_id: int, user_id: str) -> OfferResponse:
        offer = OfferService._get_offer(db, offer_id)
        proposal = OfferService._get_proposal(db, offer.proposal_id)
        if offer.runner_id != user_id and proposal.orderer_id != user_id:
            raise api_error(AppError.FORBIDDEN)
        return OfferService._to_response(db, offer)

    @staticmethod
    def list_own(
        db: Session,
        runner_id: str,
        offer_status: OfferStatus | None,
        page: int,
        size: int,
    ) -> PageResponse[OfferResponse]:
        query = db.query(Offer).filter(Offer.runner_id == runner_id)
        if offer_status is not None:
            query = query.filter(Offer.status == offer_status)

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
    def accept(db: Session, offer_id: int, orderer_id: str, request: OfferAcceptRequest) -> OfferAcceptResponse:
        offer = OfferService._get_offer(db, offer_id)
        proposal = OfferService._get_proposal(db, offer.proposal_id)

        if proposal.orderer_id != orderer_id:
            raise api_error(AppError.FORBIDDEN)

        existing_mission = (
            db.query(Mission)
            .filter((Mission.proposal_id == proposal.id) | (Mission.offer_id == offer.id))
            .first()
        )
        if existing_mission is not None:
            raise api_error(AppError.MISSION_ALREADY_EXISTS)

        if offer.status != OfferStatus.WAITING:
            raise api_error(AppError.OFFER_NOT_ACCEPTABLE)

        if proposal.status != ProposalStatus.OFFERED:
            raise api_error(AppError.PROPOSAL_NOT_MATCHABLE)

        total_amount = request.run_fee + request.item_price
        mission = Mission(
            proposal_id=proposal.id,
            offer_id=offer.id,
            orderer_id=proposal.orderer_id,
            runner_id=offer.runner_id,
            contract_amount=total_amount,
            run_fee=request.run_fee,
            item_price=request.item_price,
            total_amount=total_amount,
            status=MissionStatus.CREATED,
        )

        db.add(mission)
        offer.accept()
        proposal.status = ProposalStatus.MATCHED
        rejected_count = (
            db.query(Offer)
            .filter(
                Offer.proposal_id == proposal.id,
                Offer.id != offer.id,
                Offer.status == OfferStatus.WAITING,
            )
            .update({Offer.status: OfferStatus.REJECTED}, synchronize_session=False)
        )
        db.commit()
        db.refresh(mission)
        db.refresh(offer)
        db.refresh(proposal)

        return OfferAcceptResponse(
            proposal_id=proposal.id,
            offer_id=offer.id,
            mission_id=mission.id,
            proposal_status=proposal.status,
            accepted_offer_status=offer.status,
            rejected_offer_count=rejected_count,
            mission_status=mission.status,
            orderer_id=proposal.orderer_id,
            runner_id=offer.runner_id,
            run_fee=request.run_fee,
            item_price=request.item_price,
            total_amount=mission.total_amount,
            created_at=mission.created_at,
        )
