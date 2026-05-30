"""Proposal business logic."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.proposal import ProposalOwnOfferResponse, ProposalOwnResponse, ProposalRequest


PUBLIC_LIST_STATUSES = (ProposalStatus.POSTED, ProposalStatus.OFFERED)
DETAIL_VISIBLE_STATUSES = (
    ProposalStatus.POSTED,
    ProposalStatus.OFFERED,
    ProposalStatus.MATCHED,
    ProposalStatus.CANCELLED,
)
EDITABLE_STATUSES = (ProposalStatus.HOLDING, ProposalStatus.POSTED)
CANCELLABLE_STATUSES = (ProposalStatus.HOLDING, ProposalStatus.POSTED, ProposalStatus.OFFERED)


def _error(http_status: int, code: str, message: str, details: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=http_status,
        detail={"code": code, "message": message, "details": details},
    )


class ProposalService:
    """Service layer for Proposal commands and queries."""

    @staticmethod
    def parse_deadline(raw_deadline: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(raw_deadline.replace("Z", "+00:00"))
        except ValueError as exc:
            raise _error(
                status.HTTP_400_BAD_REQUEST,
                "INVALID_DATE_TIME_FORMAT",
                "deadline 형식이 올바르지 않습니다.",
                "deadline must be ISO-8601 with offset",
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise _error(
                status.HTTP_400_BAD_REQUEST,
                "INVALID_DATE_TIME_FORMAT",
                "deadline 형식이 올바르지 않습니다.",
                "deadline must include timezone offset",
            )

        deadline = parsed.astimezone(timezone.utc)
        if deadline <= datetime.now(timezone.utc):
            raise _error(
                status.HTTP_400_BAD_REQUEST,
                "PROPOSAL_DEADLINE_INVALID",
                "마감 시각은 현재 시각보다 이후여야 합니다.",
                None,
            )

        return deadline

    @staticmethod
    def _validate_request(request: ProposalRequest) -> datetime:
        deadline = ProposalService.parse_deadline(request.deadline)
        if request.errand_fee < 1000:
            raise _error(
                status.HTTP_400_BAD_REQUEST,
                "PROPOSAL_ERRAND_FEE_INVALID",
                "심부름비는 1000원 이상이어야 합니다.",
                "errandFee must be greater than or equal to 1000",
            )
        return deadline

    @staticmethod
    def _get_existing_user(db: Session, user_id: str) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise _error(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "User not found", None)
        return user

    @staticmethod
    def _get_proposal(db: Session, proposal_id: int) -> Proposal:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if proposal is None:
            raise _error(
                status.HTTP_404_NOT_FOUND,
                "PROPOSAL_NOT_FOUND",
                "제안을 찾을 수 없습니다.",
                f"id: {proposal_id}",
            )
        return proposal

    @staticmethod
    def _ensure_owner(proposal: Proposal, user_id: str) -> None:
        if proposal.orderer_id != user_id:
            raise _error(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "권한이 없습니다.", None)

    @staticmethod
    def list_public(db: Session, page: int, size: int) -> PageResponse[Proposal]:
        query = db.query(Proposal).filter(Proposal.status.in_(PUBLIC_LIST_STATUSES))
        total = query.count()
        items = (
            query.order_by(Proposal.created_at.desc(), Proposal.id.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return PageResponse(items=items, page=page, size=size, total=total)

    @staticmethod
    def get_detail(db: Session, proposal_id: int) -> Proposal:
        proposal = ProposalService._get_proposal(db, proposal_id)
        if proposal.status not in DETAIL_VISIBLE_STATUSES:
            raise _error(
                status.HTTP_404_NOT_FOUND,
                "PROPOSAL_NOT_FOUND",
                "제안을 찾을 수 없습니다.",
                f"id: {proposal_id}",
            )
        return proposal

    @staticmethod
    def list_own(db: Session, user_id: str, proposal_status: ProposalStatus | None) -> list[ProposalOwnResponse]:
        query = db.query(Proposal).filter(Proposal.orderer_id == user_id)
        if proposal_status is not None:
            query = query.filter(Proposal.status == proposal_status)

        proposals = query.order_by(Proposal.created_at.desc(), Proposal.id.desc()).all()
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

        return [
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

    @staticmethod
    def create(db: Session, request: ProposalRequest, orderer_id: str) -> Proposal:
        ProposalService._get_existing_user(db, orderer_id)
        deadline = ProposalService._validate_request(request)
        proposal = Proposal(
            orderer_id=orderer_id,
            title=request.title,
            content=request.content,
            deadline=deadline,
            errand_fee=request.errand_fee,
            status=ProposalStatus.HOLDING,
            meeting_at=deadline,
            item_price=0,
            deposit=0,
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
            raise _error(
                status.HTTP_409_CONFLICT,
                "PROPOSAL_NOT_EDITABLE",
                "수정할 수 없는 제안 상태입니다.",
                f"status: {proposal.status.value}",
            )

        deadline = ProposalService._validate_request(request)
        proposal.title = request.title
        proposal.content = request.content
        proposal.deadline = deadline
        proposal.errand_fee = request.errand_fee
        proposal.meeting_at = deadline
        db.commit()
        db.refresh(proposal)
        return proposal

    @staticmethod
    def cancel(db: Session, proposal_id: int, orderer_id: str) -> Proposal:
        proposal = ProposalService._get_proposal(db, proposal_id)
        ProposalService._ensure_owner(proposal, orderer_id)
        if proposal.status not in CANCELLABLE_STATUSES:
            raise _error(
                status.HTTP_409_CONFLICT,
                "PROPOSAL_NOT_CANCELLABLE",
                "취소할 수 없는 제안 상태입니다.",
                f"status: {proposal.status.value}",
            )

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
    def confirm_payment(
        db: Session, proposal_id: int, admin_id: str, depositor_name: str | None = None
    ) -> Proposal:
        proposal = ProposalService._get_proposal(db, proposal_id)
        if proposal.status != ProposalStatus.HOLDING:
            raise _error(
                status.HTTP_400_BAD_REQUEST,
                "INVALID_STATUS",
                "입금 확인 대기 상태가 아닙니다.",
                f"current status: {proposal.status.value}",
            )
        proposal.status = ProposalStatus.POSTED
        db.commit()
        db.refresh(proposal)
        return proposal

    @staticmethod
    def delete_expired_proposals(db: Session) -> int:
        """Payment expiry cleanup is outside the current Proposal API scope."""

        return 0
