"""Mission business logic."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.mission import Mission, MissionStatus
from app.models.offer import Offer, OfferStatus
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.mission import MissionAction, MissionResponse, MissionRole, MissionUpdateRequest, MissionUserSummary


def _error(http_status: int, code: str, message: str, details: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=http_status,
        detail={"code": code, "message": message, "details": details},
    )


class MissionService:
    """Service layer for Mission queries and state transitions."""

    @staticmethod
    def _get_mission(db: Session, mission_id: int) -> Mission:
        mission = db.query(Mission).filter(Mission.id == mission_id).first()
        if mission is None:
            raise _error(status.HTTP_404_NOT_FOUND, "MISSION_NOT_FOUND", "미션을 찾을 수 없습니다.", None)
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
            run_fee=mission.run_fee,
            item_price=mission.item_price,
            total_amount=mission.total_amount,
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
            raise _error(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "권한이 없습니다.", None)

        if request.action == MissionAction.START_PROGRESS:
            MissionService._ensure_runner(mission, user_id)
            if not mission.can_start():
                raise MissionService._not_updatable()
            mission.start_progress()

        elif request.action == MissionAction.COMPLETE_DELIVERY:
            MissionService._ensure_runner(mission, user_id)
            if not request.proof_image_url:
                raise _error(
                    status.HTTP_400_BAD_REQUEST,
                    "VALIDATION_ERROR",
                    "요청 값이 올바르지 않습니다.",
                    "proofImageUrl: Field required",
                )
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
                raise _error(
                    status.HTTP_400_BAD_REQUEST,
                    "VALIDATION_ERROR",
                    "요청 값이 올바르지 않습니다.",
                    "disputeReason: Field required",
                )
            if not mission.can_raise_dispute():
                raise MissionService._not_updatable()
            mission.raise_dispute(request.dispute_reason)

        db.commit()
        db.refresh(mission)
        return MissionService._to_response(db, mission)

    @staticmethod
    def _ensure_runner(mission: Mission, user_id: str) -> None:
        if mission.runner_id != user_id:
            raise _error(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "권한이 없습니다.", None)

    @staticmethod
    def _ensure_orderer(mission: Mission, user_id: str) -> None:
        if mission.orderer_id != user_id:
            raise _error(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "권한이 없습니다.", None)

    @staticmethod
    def _not_updatable() -> HTTPException:
        return _error(status.HTTP_409_CONFLICT, "MISSION_NOT_UPDATABLE", "업데이트할 수 없는 미션 상태입니다.", None)

    @staticmethod
    def _complete_offer_if_needed(db: Session, mission: Mission) -> None:
        if mission.status != MissionStatus.COMPLETED:
            return

        offer = db.query(Offer).filter(Offer.id == mission.offer_id).first()
        if offer is not None and offer.status == OfferStatus.ACCEPTED:
            offer.status = OfferStatus.COMPLETED
