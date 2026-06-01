"""Terms agreement service layer."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import AppError, api_error
from app.models.terms import TermsAgreement, TermsType
from app.models.user import User
from app.schemas.terms import TermsAgreementRequest, TermsAgreementResponse


class TermsAgreementService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    def agree(self, user: User, payload: TermsAgreementRequest) -> TermsAgreementResponse:
        existing_user = self.db.query(User).filter(User.id == str(user.id)).first()
        if existing_user is None:
            raise api_error(AppError.USER_NOT_FOUND)

        payload_by_field = {
            TermsType.TERMS_OF_SERVICE.field_name: payload.terms_of_service,
            TermsType.PRIVACY_POLICY.field_name: payload.privacy_policy,
            TermsType.PAYMENT_REFUND_POLICY.field_name: payload.payment_refund_policy,
        }
        for terms_type in TermsType:
            if terms_type.required and payload_by_field.get(terms_type.field_name) is not True:
                raise api_error(AppError.REQUIRED_TERMS_INVALID)

        now = self._now()
        agreement = (
            self.db.query(TermsAgreement)
            .filter(TermsAgreement.user_id == str(existing_user.id))
            .first()
        )

        if agreement is None:
            agreement = TermsAgreement(user_id=str(existing_user.id))
            self.db.add(agreement)

        agreement.terms_of_service = payload.terms_of_service
        agreement.privacy_policy = payload.privacy_policy
        agreement.payment_refund_policy = payload.payment_refund_policy
        agreement.agreed_at = now

        self.db.commit()
        self.db.refresh(agreement)

        return TermsAgreementResponse(
            user_id=agreement.user_id,
            terms_of_service=agreement.terms_of_service,
            privacy_policy=agreement.privacy_policy,
            payment_refund_policy=agreement.payment_refund_policy,
            agreed_at=agreement.agreed_at,
        )
