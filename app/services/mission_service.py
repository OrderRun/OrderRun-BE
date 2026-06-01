"""Mission business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import AppError, api_error
from app.models.mission import Mission, MissionStatus
from app.models.offer import Offer, OfferStatus
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.mission import MissionAction, MissionResponse, MissionRole, MissionUpdateRequest, MissionUserSummary


class MissionService:
    """Service layer for Mission queries and state transitions."""

    @staticmethod
    def _get_mission(db: Session, mission_id: int) -> Mission:
        mission = db.query(Mission).filter(Mission.id == mission_id).first()
        if mission is None:
            raise api_error(AppError.MISSION_NOT_FOUND)
        return mission

    @staticmethod
    def _user_summary(db: Session, user_id: str) -> MissionUserSummary:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            return MissionUserSummary(id=user_id, name="", phone=None)
        return MissionUserSummary(id=user.id, name=user.name, phone=user.phone)

    @staticmethod
    def _to_response(db: Session, mission: Mission) -> MissionResponse:
        return MissionResponse(
            id=mission.id,
            proposal_id=mission.proposal_id,
            offer_id=mission.offer_id,
            orderer=MissionService._user_summary(db, mission.orderer_id),
            runner=MissionService._user_summary(db, mission.runner_id),
            delivery_proof_image_url=mission.delivery_proof_image_url,
            status=mission.status,
            pickup_at=mission.pickup_at,
            delivery_completed_at=mission.delivery_completed_at,
            received_confirmed_at=mission.received_confirmed_at,
            settled_at=mission.settled_at,
            dispute_reason=mission.dispute_reason,
            created_at=mission.created_at,
        )

    @staticmethod
    def list_own(
        db: Session,
        user_id: str,
        role: MissionRole,
        mission_status: MissionStatus | None,
        page: int,
        size: int,
    ) -> PageResponse[MissionResponse]:
        query = db.query(Mission)
        if role == MissionRole.ORDERER:
            query = query.filter(Mission.orderer_id == user_id)
        elif role == MissionRole.RUNNER:
            query = query.filter(Mission.runner_id == user_id)

        if mission_status is not None:
            query = query.filter(Mission.status == mission_status)

        total = query.count()
        missions = (
            query.order_by(Mission.created_at.desc(), Mission.id.desc())
            .offset(page * size)
            .limit(size)
            .all()
        )
        return PageResponse.of(
            content=[MissionService._to_response(db, mission) for mission in missions],
            page_number=page,
            page_size=size,
            total_elements=total,
        )

    @staticmethod
    def update_status(
        db: Session,
        mission_id: int,
        user_id: str,
        request: MissionUpdateRequest,
    ) -> MissionResponse:
        mission = MissionService._get_mission(db, mission_id)

        if user_id not in {mission.orderer_id, mission.runner_id}:
            raise api_error(AppError.FORBIDDEN)

        if request.action == MissionAction.START_PROGRESS:
            MissionService._ensure_runner(mission, user_id)
            if not mission.can_start():
                raise MissionService._not_updatable()
            mission.start_progress()

        elif request.action == MissionAction.COMPLETE_DELIVERY:
            MissionService._ensure_runner(mission, user_id)
            if not request.proof_image_url:
                raise api_error(AppError.MISSION_PROOF_IMAGE_REQUIRED, "proofImageUrl: Field required")
            if not mission.can_complete_delivery():
                raise MissionService._not_updatable()
            mission.complete_delivery(request.proof_image_url)
            MissionService._complete_offer_if_needed(db, mission)

        elif request.action == MissionAction.CONFIRM_RECEIVED:
            MissionService._ensure_orderer(mission, user_id)
            if not mission.can_confirm_receipt():
                raise MissionService._not_updatable()
            mission.confirm_receipt()
            MissionService._complete_offer_if_needed(db, mission)

        elif request.action == MissionAction.DISPUTE:
            if not request.dispute_reason:
                raise api_error(AppError.MISSION_DISPUTE_REASON_REQUIRED, "disputeReason: Field required")
            if not mission.can_raise_dispute():
                raise MissionService._not_updatable()
            mission.raise_dispute(request.dispute_reason)

        db.commit()
        db.refresh(mission)
        return MissionService._to_response(db, mission)

    @staticmethod
    def _ensure_runner(mission: Mission, user_id: str) -> None:
        if mission.runner_id != user_id:
            raise api_error(AppError.FORBIDDEN)

    @staticmethod
    def _ensure_orderer(mission: Mission, user_id: str) -> None:
        if mission.orderer_id != user_id:
            raise api_error(AppError.FORBIDDEN)

    @staticmethod
    def _not_updatable():
        return api_error(AppError.MISSION_NOT_UPDATABLE)

    @staticmethod
    def _complete_offer_if_needed(db: Session, mission: Mission) -> None:
        if mission.status != MissionStatus.COMPLETED:
            return

        offer = db.query(Offer).filter(Offer.id == mission.offer_id).first()
        if offer is not None and offer.status == OfferStatus.ACCEPTED:
            offer.status = OfferStatus.COMPLETED
