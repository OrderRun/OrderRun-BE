"""Persistence and delivery orchestration for phone verification."""

from __future__ import annotations

import logging

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.errors import AppError, api_error
from app.core.time import utcnow_naive
from app.models.user import (
    AuthPhoneVerification,
    PhoneVerificationPurpose,
    PhoneVerificationStatus,
)
from app.schemas.user import AuthVerificationSendResponse
from app.services.phone_verification import (
    VERIFICATION_CODE_MAX_ATTEMPTS,
    VERIFICATION_CODE_TTL,
    build_verification_message,
    generate_verification_code,
    hash_verification_code,
)
from app.services.sms_service import SmsSender


logger = logging.getLogger(__name__)


class PhoneVerificationService:
    """Owns verification records and the SMS delivery adapter."""

    def __init__(self, sms_sender: SmsSender | None):
        self.sms_sender = sms_sender

    def send(
        self,
        db: Session,
        purpose: PhoneVerificationPurpose,
        phone: str,
        background_tasks: BackgroundTasks,
        *,
        name: str | None = None,
        carrier: str | None = None,
    ) -> AuthVerificationSendResponse:
        if self.has_active_pending(db, purpose, phone):
            raise api_error(AppError.PHONE_VERIFICATION_ALREADY_SENT)
        if self.sms_sender is None:
            raise api_error(AppError.SMS_SENDER_NOT_CONFIGURED)

        code = generate_verification_code()
        now = utcnow_naive()
        verification = AuthPhoneVerification(
            purpose=purpose,
            phone=phone,
            name=name,
            carrier=carrier,
            code_hash=hash_verification_code(code),
            status=PhoneVerificationStatus.PENDING,
            expires_at=now + VERIFICATION_CODE_TTL,
            sent_at=now,
            attempt_count=0,
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)

        background_tasks.add_task(self._send_sms_safely, phone, build_verification_message(code))
        return AuthVerificationSendResponse(phone=phone, expires_at=verification.expires_at)

    @staticmethod
    def has_active_pending(
        db: Session,
        purpose: PhoneVerificationPurpose,
        phone: str,
    ) -> bool:
        now = utcnow_naive()
        return (
            db.query(AuthPhoneVerification)
            .filter(
                AuthPhoneVerification.purpose == purpose,
                AuthPhoneVerification.phone == phone,
                AuthPhoneVerification.status == PhoneVerificationStatus.PENDING,
                AuthPhoneVerification.expires_at > now,
            )
            .first()
            is not None
        )

    @staticmethod
    def verify(
        db: Session,
        purpose: PhoneVerificationPurpose,
        phone: str,
        code: str,
    ) -> AuthPhoneVerification:
        verification = (
            db.query(AuthPhoneVerification)
            .filter(
                AuthPhoneVerification.purpose == purpose,
                AuthPhoneVerification.phone == phone,
                AuthPhoneVerification.status == PhoneVerificationStatus.PENDING,
            )
            .order_by(AuthPhoneVerification.sent_at.desc(), AuthPhoneVerification.id.desc())
            .first()
        )
        if verification is None:
            raise api_error(AppError.PHONE_VERIFICATION_NOT_FOUND)

        now = utcnow_naive()
        if verification.expires_at <= now:
            verification.status = PhoneVerificationStatus.EXPIRED
            db.commit()
            raise api_error(AppError.PHONE_VERIFICATION_EXPIRED)

        if verification.code_hash != hash_verification_code(code):
            verification.attempt_count += 1
            if verification.attempt_count >= VERIFICATION_CODE_MAX_ATTEMPTS:
                verification.status = PhoneVerificationStatus.EXPIRED
            db.commit()
            raise api_error(AppError.PHONE_VERIFICATION_CODE_MISMATCH)

        verification.status = PhoneVerificationStatus.VERIFIED
        verification.verified_at = now
        return verification

    def _send_sms_safely(self, phone: str, message: str) -> None:
        if self.sms_sender is None:
            logger.error("SMS sender not configured")
            return
        try:
            self.sms_sender.send(phone, message)
        except Exception:
            logger.exception("SMS sending failed")
