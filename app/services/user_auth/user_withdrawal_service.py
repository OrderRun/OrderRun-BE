"""Transactional user withdrawal orchestration."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import AppError, api_error
from app.core.time import utcnow_naive
from app.models.notification import Notification
from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.settlement import SettlementAccount
from app.models.user import (
    AuthPhoneVerification,
    User,
    UserFCMToken,
    UserWithdrawal,
    UserWithdrawalReasonQuestion,
)
from app.schemas.user import UserWithdrawalReasonQuestionResponse, UserWithdrawalRequest


WITHDRAWAL_BLOCKING_PROPOSAL_STATUSES = {
    ProposalStatus.MATCHED,
    ProposalStatus.ORDER_COMPLETED,
    ProposalStatus.DISPUTED,
}
WITHDRAWAL_BLOCKING_OFFER_STATUSES = {
    OfferStatus.ACCEPTED,
    OfferStatus.RUNNER_COMPLETED,
    OfferStatus.DISPUTED,
}
WITHDRAWAL_AUTO_CANCEL_PROPOSAL_STATUSES = {
    ProposalStatus.HOLDING,
    ProposalStatus.POSTED,
    ProposalStatus.OFFERED,
}
WITHDRAWAL_AUTO_CANCEL_OFFER_STATUSES = {OfferStatus.WAITING}


class UserWithdrawalService:
    @staticmethod
    def list_reason_questions(db: Session) -> list[UserWithdrawalReasonQuestionResponse]:
        questions = (
            db.query(UserWithdrawalReasonQuestion)
            .filter(UserWithdrawalReasonQuestion.is_active.is_(True))
            .order_by(UserWithdrawalReasonQuestion.display_order.asc(), UserWithdrawalReasonQuestion.id.asc())
            .all()
        )
        return [UserWithdrawalReasonQuestionResponse.model_validate(question) for question in questions]

    @staticmethod
    def withdraw_user(db: Session, user: User, request: UserWithdrawalRequest | None = None) -> None:
        fresh_user = db.query(User).filter(User.id == str(user.id), User.deleted.is_(False)).first()
        if fresh_user is None:
            raise api_error(AppError.USER_NOT_FOUND)

        user_id = str(fresh_user.id)
        if UserWithdrawalService._has_blocking_activity(db, user_id):
            raise api_error(AppError.USER_WITHDRAWAL_BLOCKED)

        reason_question = UserWithdrawalService._validate_request(db, request)
        original_phone = fresh_user.phone
        withdrawn_at = utcnow_naive()
        try:
            UserWithdrawalService._auto_cancel_pre_match_activity(db, user_id)
            db.add(
                UserWithdrawal(
                    user_id=user_id,
                    reason_question_id=reason_question.id if reason_question is not None else None,
                    detail_reason=request.detail_reason if request is not None else None,
                    withdrawn_at=withdrawn_at,
                )
            )
            if original_phone is not None:
                db.query(AuthPhoneVerification).filter(AuthPhoneVerification.phone == original_phone).delete(
                    synchronize_session=False
                )
            db.query(UserFCMToken).filter(UserFCMToken.user_id == user_id).delete(synchronize_session=False)
            db.query(SettlementAccount).filter(SettlementAccount.user_id == user_id).delete(
                synchronize_session=False
            )
            db.query(Notification).filter(Notification.user_id == user_id).delete(synchronize_session=False)
            fresh_user.withdraw(withdrawn_at)
            db.commit()
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def _validate_request(
        db: Session, request: UserWithdrawalRequest | None
    ) -> UserWithdrawalReasonQuestion | None:
        if request is None or request.reason_question_id is None:
            return None

        question = (
            db.query(UserWithdrawalReasonQuestion)
            .filter(
                UserWithdrawalReasonQuestion.id == request.reason_question_id,
                UserWithdrawalReasonQuestion.is_active.is_(True),
            )
            .one_or_none()
        )
        if question is None:
            raise api_error(AppError.VALIDATION_ERROR, "reasonQuestionId")
        if question.requires_detail and request.detail_reason is None:
            raise api_error(AppError.VALIDATION_ERROR, "detailReason")
        return question

    @staticmethod
    def _has_blocking_activity(db: Session, user_id: str) -> bool:
        has_blocking_proposal = (
            db.query(Proposal.id)
            .filter(
                Proposal.orderer_id == user_id,
                Proposal.status.in_(WITHDRAWAL_BLOCKING_PROPOSAL_STATUSES),
            )
            .first()
            is not None
        )
        if has_blocking_proposal:
            return True

        return (
            db.query(Offer.id)
            .filter(
                Offer.runner_id == user_id,
                Offer.status.in_(WITHDRAWAL_BLOCKING_OFFER_STATUSES),
            )
            .first()
            is not None
        )

    @staticmethod
    def _auto_cancel_pre_match_activity(db: Session, user_id: str) -> None:
        proposals = (
            db.query(Proposal)
            .filter(
                Proposal.orderer_id == user_id,
                Proposal.status.in_(WITHDRAWAL_AUTO_CANCEL_PROPOSAL_STATUSES),
            )
            .all()
        )
        proposal_ids = [proposal.id for proposal in proposals]
        if proposal_ids:
            waiting_offers = (
                db.query(Offer)
                .filter(
                    Offer.proposal_id.in_(proposal_ids),
                    Offer.status.in_(WITHDRAWAL_AUTO_CANCEL_OFFER_STATUSES),
                )
                .all()
            )
            for offer in waiting_offers:
                offer.cancel()
            for proposal in proposals:
                proposal.cancel()

        runner_offers = (
            db.query(Offer)
            .filter(
                Offer.runner_id == user_id,
                Offer.status.in_(WITHDRAWAL_AUTO_CANCEL_OFFER_STATUSES),
            )
            .all()
        )
        for offer in runner_offers:
            offer.cancel()
