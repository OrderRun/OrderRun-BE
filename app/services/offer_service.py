"""Offer business logic."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError, api_error
from app.events.base import EventBus
from app.events.offer_events import OfferAcceptedEvent, OfferCreatedEvent
from app.models.mission import Mission, MissionStatus
from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.offer import OfferAcceptResponse, OfferCreate, OfferResponse


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
    def _ensure_proposal_exists(db: Session, proposal_id: int) -> None:
        OfferService._get_proposal(db, proposal_id)

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
    def _mission_id(db: Session, offer_id: int) -> int | None:
        mission = db.query(Mission).filter(Mission.offer_id == offer_id).first()
        return mission.id if mission is not None else None

    @staticmethod
    def _to_response(db: Session, offer: Offer) -> OfferResponse:
        return OfferResponse(
            id=offer.id,
            proposal_id=offer.proposal_id,
            runner_id=offer.runner_id,
            runner_name=OfferService._runner_name(db, offer.runner_id),
            status=offer.status,
            mission_id=OfferService._mission_id(db, offer.id),
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
    ) -> list[OfferResponse]:
        OfferService._ensure_proposal_exists(db, proposal_id)
        query = db.query(Offer).filter(Offer.proposal_id == proposal_id)
        if offer_statuses:
            query = query.filter(Offer.status.in_(offer_statuses))

        offers = query.order_by(Offer.created_at.desc(), Offer.id.desc()).all()
        return [OfferService._to_response(db, offer) for offer in offers]

    @staticmethod
    def get_offer_detail(db: Session, offer_id: int, user_id: str) -> OfferResponse:
        offer = OfferService._get_offer(db, offer_id)
        proposal = OfferService._get_proposal(db, offer.proposal_id)
        if offer.runner_id != user_id and proposal.orderer_id != user_id:
            raise api_error(AppError.FORBIDDEN)
        return OfferService._to_response(db, offer)

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

        rejected_runner_ids = tuple(
            row[0] for row in db.query(Offer.runner_id).filter(
                Offer.proposal_id == proposal.id,
                Offer.id != offer.id,
                Offer.status == OfferStatus.WAITING,
            ).all()
        )

        mission = Mission(
            proposal_id=proposal.id,
            offer_id=offer.id,
            orderer_id=proposal.orderer_id,
            runner_id=offer.runner_id,
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
            created_at=mission.created_at,
        )
