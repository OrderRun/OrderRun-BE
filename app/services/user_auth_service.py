"""Phone-auth and user account service layer."""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError, api_error
from app.core.phone import normalize_phone
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.models.user import (
    AuthPhoneVerification,
    PhoneVerificationPurpose,
    PhoneVerificationStatus,
    User,
    UserFCMToken,
)
from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.notification import Notification
from app.models.settlement import SettlementAccount
from app.schemas.user import (
    AuthAccessTokenResponse,
    AuthLoginConfirmRequest,
    AuthLoginSendRequest,
    AuthPhoneConfirmRequest,
    AuthRefreshRequest,
    AuthSignupSendRequest,
    AuthTokenResponse,
    AuthVerificationSendResponse,
    UserDetailResponse,
)
from app.services.sms_service import SmsSender


logger = logging.getLogger(__name__)

LOCAL_TEST_VERIFICATION_CODE = "123456"
LOGIN_TEST_CODE_ALLOWED_ENVS = {"development", "local", "staging"}
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


class UserAuthService:
    def __init__(self, db: Session, sms_sender: SmsSender | None = None):
        self.db = db
        self.sms_sender = sms_sender

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _code_ttl() -> timedelta:
        return timedelta(minutes=5)

    @staticmethod
    def _access_expires_in_ms() -> int:
        return settings.jwt_access_token_expire_minutes * 60 * 1000

    @staticmethod
    def _generate_code() -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    @staticmethod
    def _hash_code(code: str) -> str:
        digest = hashlib.sha256(f"{settings.secret_key}:{code}".encode("utf-8")).hexdigest()
        return digest

    @staticmethod
    def _is_login_test_code_allowed(code: str) -> bool:
        return code == LOCAL_TEST_VERIFICATION_CODE and settings.app_env.lower() in LOGIN_TEST_CODE_ALLOWED_ENVS

    @staticmethod
    def _message(code: str) -> str:
        return f"[OrderRun] 인증번호는 {code} 입니다. 5분 내 입력해 주세요."

    def _send_sms_safely(self, phone: str, message: str) -> None:
        if self.sms_sender is None:
            logger.error("SMS sender not configured")
            return
        try:
            self.sms_sender.send(phone, message)
        except Exception:
            logger.exception("SMS sending failed")

    def _find_user_by_phone(self, phone: str) -> User | None:
        return self.db.query(User).filter(User.phone == phone, User.deleted.is_(False)).first()

    def _latest_pending_verification(
        self,
        purpose: PhoneVerificationPurpose,
        phone: str,
    ) -> AuthPhoneVerification | None:
        return (
            self.db.query(AuthPhoneVerification)
            .filter(
                AuthPhoneVerification.purpose == purpose,
                AuthPhoneVerification.phone == phone,
                AuthPhoneVerification.status == PhoneVerificationStatus.PENDING,
            )
            .order_by(AuthPhoneVerification.sent_at.desc(), AuthPhoneVerification.id.desc())
            .first()
        )

    def _has_active_pending_verification(
        self,
        purpose: PhoneVerificationPurpose,
        phone: str,
    ) -> bool:
        now = self._now()
        return (
            self.db.query(AuthPhoneVerification)
            .filter(
                AuthPhoneVerification.purpose == purpose,
                AuthPhoneVerification.phone == phone,
                AuthPhoneVerification.status == PhoneVerificationStatus.PENDING,
                AuthPhoneVerification.expires_at > now,
            )
            .first()
            is not None
        )

    def _send_verification(
        self,
        purpose: PhoneVerificationPurpose,
        phone: str,
        name: str | None = None,
        carrier: str | None = None,
        background_tasks: BackgroundTasks | None = None,
    ) -> AuthVerificationSendResponse:
        if self.sms_sender is None:
            raise api_error(AppError.SMS_SENDER_NOT_CONFIGURED)

        code = self._generate_code()
        message = self._message(code)
        now = self._now()
        verification = AuthPhoneVerification(
            purpose=purpose,
            phone=phone,
            name=name,
            carrier=carrier,
            code_hash=self._hash_code(code),
            status=PhoneVerificationStatus.PENDING,
            expires_at=now + self._code_ttl(),
            sent_at=now,
            attempt_count=0,
        )
        self.db.add(verification)

        self.db.commit()
        self.db.refresh(verification)
        if background_tasks is not None:
            background_tasks.add_task(self._send_sms_safely, phone, message)
        else:
            self._send_sms_safely(phone, message)
        return AuthVerificationSendResponse(phone=phone, expires_at=verification.expires_at)

    def send_signup_verification(
        self,
        payload: AuthSignupSendRequest,
        background_tasks: BackgroundTasks | None = None,
    ) -> AuthVerificationSendResponse:
        phone = normalize_phone(payload.phone)
        if self._find_user_by_phone(phone) is not None:
            raise api_error(AppError.PHONE_ALREADY_EXISTS)
        if self._has_active_pending_verification(PhoneVerificationPurpose.SIGNUP, phone):
            raise api_error(AppError.PHONE_VERIFICATION_ALREADY_SENT)
        return self._send_verification(
            purpose=PhoneVerificationPurpose.SIGNUP,
            phone=phone,
            name=payload.name.strip(),
            carrier=payload.carrier.strip(),
            background_tasks=background_tasks,
        )

    def send_login_verification(
        self,
        payload: AuthLoginSendRequest,
        background_tasks: BackgroundTasks | None = None,
    ) -> AuthVerificationSendResponse:
        phone = normalize_phone(payload.phone)
        user = self._find_user_by_phone(phone)
        if user is None:
            raise api_error(AppError.INVALID_CREDENTIALS)
        if self._has_active_pending_verification(PhoneVerificationPurpose.LOGIN, phone):
            raise api_error(AppError.PHONE_VERIFICATION_ALREADY_SENT)
        return self._send_verification(
            purpose=PhoneVerificationPurpose.LOGIN,
            phone=phone,
            background_tasks=background_tasks,
        )

    def _confirm_verification(
        self,
        purpose: PhoneVerificationPurpose,
        phone: str,
        code: str,
    ) -> AuthPhoneVerification:
        verification = self._latest_pending_verification(purpose, phone)
        if verification is None:
            raise api_error(AppError.PHONE_VERIFICATION_NOT_FOUND)

        now = self._now()
        if verification.expires_at <= now:
            verification.status = PhoneVerificationStatus.EXPIRED
            self.db.commit()
            raise api_error(AppError.PHONE_VERIFICATION_EXPIRED)

        if verification.code_hash != self._hash_code(code):
            verification.attempt_count += 1
            if verification.attempt_count >= 5:
                verification.status = PhoneVerificationStatus.EXPIRED
            self.db.commit()
            raise api_error(AppError.PHONE_VERIFICATION_CODE_MISMATCH)

        verification.status = PhoneVerificationStatus.VERIFIED
        verification.verified_at = now
        return verification

    def _build_tokens(self, user: User) -> AuthTokenResponse:
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        return AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=self._access_expires_in_ms(),
            user_id=str(user.id),
        )

    def confirm_signup(self, payload: AuthPhoneConfirmRequest) -> AuthTokenResponse:
        phone = normalize_phone(payload.phone)
        verification = self._confirm_verification(PhoneVerificationPurpose.SIGNUP, phone, payload.code)

        if self._find_user_by_phone(phone) is not None:
            self.db.rollback()
            raise api_error(AppError.PHONE_ALREADY_EXISTS)

        now = self._now()
        user = User(
            name=verification.name or "",
            phone=phone,
            phone_verified_at=now,
            last_login_at=now,
            alarm_enabled=False,
        )
        self.db.add(user)
        try:
            self.db.commit()
        except Exception as exc:  # pragma: no cover - defensive transactional guard
            self.db.rollback()
            raise api_error(AppError.PHONE_ALREADY_EXISTS) from exc

        self.db.refresh(user)
        return self._build_tokens(user)

    def confirm_login(self, payload: AuthLoginConfirmRequest) -> AuthTokenResponse:
        phone = normalize_phone(payload.phone)
        user = self._find_user_by_phone(phone)
        if user is None:
            raise api_error(AppError.USER_NOT_FOUND)

        if not self._is_login_test_code_allowed(payload.code):
            self._confirm_verification(PhoneVerificationPurpose.LOGIN, phone, payload.code)

        now = self._now()
        user.update_last_login_at(now)
        if payload.fcm_token is not None:
            self._upsert_fcm_token(user.id, payload.fcm_token)

        self.db.commit()
        self.db.refresh(user)
        return self._build_tokens(user)

    def refresh_access_token(self, payload: AuthRefreshRequest) -> AuthAccessTokenResponse:
        token_payload = verify_token(payload.refresh_token, token_type="refresh")
        user_id = token_payload.get("sub")
        if not user_id:
            raise api_error(AppError.INVALID_TOKEN)

        user = self.db.query(User).filter(User.id == str(user_id), User.deleted.is_(False)).first()
        if user is None:
            raise api_error(AppError.USER_NOT_FOUND)

        access_token = create_access_token({"sub": str(user.id)})
        return AuthAccessTokenResponse(access_token=access_token, expires_in=self._access_expires_in_ms())

    def get_user_detail(self, user: User) -> UserDetailResponse:
        fresh_user = self.db.query(User).filter(User.id == str(user.id), User.deleted.is_(False)).first()
        if fresh_user is None:
            raise api_error(AppError.USER_NOT_FOUND)

        return UserDetailResponse(
            id=str(fresh_user.id),
            name=fresh_user.name,
            phone=fresh_user.phone,
            phone_verified_at=fresh_user.phone_verified_at,
            created_at=fresh_user.created_at,
            last_login_at=fresh_user.last_login_at,
            alarm_enabled=fresh_user.alarm_enabled,
            level=fresh_user.level,
        )

    def update_alarm(self, user: User, alarm_enabled: bool) -> None:
        fresh_user = self.db.query(User).filter(User.id == str(user.id), User.deleted.is_(False)).first()
        if fresh_user is None:
            raise api_error(AppError.USER_NOT_FOUND)

        fresh_user.update_alarm_setting(alarm_enabled)
        self.db.commit()

    def update_name(self, user: User, name: str) -> None:
        fresh_user = self.db.query(User).filter(User.id == str(user.id), User.deleted.is_(False)).first()
        if fresh_user is None:
            raise api_error(AppError.USER_NOT_FOUND)

        fresh_user.name = name.strip()
        self.db.commit()

    def withdraw_user(self, user: User) -> None:
        fresh_user = self.db.query(User).filter(User.id == str(user.id), User.deleted.is_(False)).first()
        if fresh_user is None:
            raise api_error(AppError.USER_NOT_FOUND)

        user_id = str(fresh_user.id)
        if self._has_blocking_activity(user_id):
            raise api_error(AppError.USER_WITHDRAWAL_BLOCKED)

        original_phone = fresh_user.phone
        self._auto_cancel_pre_match_activity(user_id)
        if original_phone is not None:
            self.db.query(AuthPhoneVerification).filter(AuthPhoneVerification.phone == original_phone).delete(
                synchronize_session=False
            )
        self.db.query(UserFCMToken).filter(UserFCMToken.user_id == user_id).delete(synchronize_session=False)
        self.db.query(SettlementAccount).filter(SettlementAccount.user_id == user_id).delete(synchronize_session=False)
        self.db.query(Notification).filter(Notification.user_id == user_id).delete(synchronize_session=False)
        fresh_user.withdraw(self._now())
        self.db.commit()

    def _has_blocking_activity(self, user_id: str) -> bool:
        has_blocking_proposal = (
            self.db.query(Proposal.id)
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
            self.db.query(Offer.id)
            .filter(
                Offer.runner_id == user_id,
                Offer.status.in_(WITHDRAWAL_BLOCKING_OFFER_STATUSES),
            )
            .first()
            is not None
        )

    def _auto_cancel_pre_match_activity(self, user_id: str) -> None:
        proposal_ids = [
            proposal_id
            for (proposal_id,) in (
                self.db.query(Proposal.id)
                .filter(
                    Proposal.orderer_id == user_id,
                    Proposal.status.in_(WITHDRAWAL_AUTO_CANCEL_PROPOSAL_STATUSES),
                )
                .all()
            )
        ]
        if proposal_ids:
            (
                self.db.query(Offer)
                .filter(
                    Offer.proposal_id.in_(proposal_ids),
                    Offer.status.in_(WITHDRAWAL_AUTO_CANCEL_OFFER_STATUSES),
                )
                .update({Offer.status: OfferStatus.CANCELLED}, synchronize_session=False)
            )
            (
                self.db.query(Proposal)
                .filter(Proposal.id.in_(proposal_ids))
                .update({Proposal.status: ProposalStatus.CANCELLED}, synchronize_session=False)
            )

        (
            self.db.query(Offer)
            .filter(
                Offer.runner_id == user_id,
                Offer.status.in_(WITHDRAWAL_AUTO_CANCEL_OFFER_STATUSES),
            )
            .update({Offer.status: OfferStatus.CANCELLED}, synchronize_session=False)
        )

    def upsert_fcm_token(self, user: User, fcm_token: str) -> None:
        fresh_user = self.db.query(User).filter(User.id == str(user.id), User.deleted.is_(False)).first()
        if fresh_user is None:
            raise api_error(AppError.USER_NOT_FOUND)

        self._upsert_fcm_token(fresh_user.id, fcm_token.strip())
        self.db.commit()

    def _upsert_fcm_token(self, user_id: str, fcm_token: str) -> None:
        token = self.db.query(UserFCMToken).filter(UserFCMToken.user_id == str(user_id)).first()
        if token is None:
            token = UserFCMToken(user_id=str(user_id), fcm_token=fcm_token)
            self.db.add(token)
        else:
            token.fcm_token = fcm_token
