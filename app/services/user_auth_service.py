"""Phone-auth and user account service layer."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.phone import normalize_phone
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.models.user import (
    AuthPhoneVerification,
    PhoneVerificationPurpose,
    PhoneVerificationStatus,
    User,
    UserFCMToken,
)
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
from app.services.sms_service import NoopSmsSender, SmsSender


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": None},
    )


class UserAuthService:
    def __init__(self, db: Session, sms_sender: SmsSender | None = None):
        self.db = db
        self.sms_sender = sms_sender or NoopSmsSender()

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
    def _message(code: str) -> str:
        return f"[OrderRun] 인증번호는 {code} 입니다. 5분 내 입력해 주세요."

    def _find_user_by_phone(self, phone: str) -> User | None:
        return self.db.query(User).filter(User.phone == phone).first()

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
    ) -> AuthVerificationSendResponse:
        code = self._generate_code()
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

        try:
            self.sms_sender.send(phone, self._message(code))
        except Exception as exc:  # pragma: no cover - provider failure is injected in tests
            self.db.rollback()
            raise _error(status.HTTP_502_BAD_GATEWAY, "SMS_SEND_FAILED", "SMS sending failed") from exc

        self.db.commit()
        self.db.refresh(verification)
        return AuthVerificationSendResponse(phone=phone, expires_at=verification.expires_at)

    def send_signup_verification(self, payload: AuthSignupSendRequest) -> AuthVerificationSendResponse:
        phone = normalize_phone(payload.phone)
        if self._find_user_by_phone(phone) is not None:
            raise _error(status.HTTP_409_CONFLICT, "PHONE_ALREADY_EXISTS", "Phone number already exists")
        if self._has_active_pending_verification(PhoneVerificationPurpose.SIGNUP, phone):
            raise _error(
                status.HTTP_409_CONFLICT,
                "PHONE_VERIFICATION_ALREADY_SENT",
                "Verification already sent",
            )
        return self._send_verification(
            purpose=PhoneVerificationPurpose.SIGNUP,
            phone=phone,
            name=payload.name.strip(),
            carrier=payload.carrier.strip(),
        )

    def send_login_verification(self, payload: AuthLoginSendRequest) -> AuthVerificationSendResponse:
        phone = normalize_phone(payload.phone)
        user = self._find_user_by_phone(phone)
        if user is None:
            raise _error(status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS", "Invalid credentials")
        if self._has_active_pending_verification(PhoneVerificationPurpose.LOGIN, phone):
            raise _error(
                status.HTTP_409_CONFLICT,
                "PHONE_VERIFICATION_ALREADY_SENT",
                "Verification already sent",
            )
        return self._send_verification(purpose=PhoneVerificationPurpose.LOGIN, phone=phone)

    def _confirm_verification(
        self,
        purpose: PhoneVerificationPurpose,
        phone: str,
        code: str,
    ) -> AuthPhoneVerification:
        verification = self._latest_pending_verification(purpose, phone)
        if verification is None:
            raise _error(
                status.HTTP_404_NOT_FOUND,
                "PHONE_VERIFICATION_NOT_FOUND",
                "Phone verification not found",
            )

        now = self._now()
        if verification.expires_at <= now:
            verification.status = PhoneVerificationStatus.EXPIRED
            self.db.commit()
            raise _error(
                status.HTTP_400_BAD_REQUEST,
                "PHONE_VERIFICATION_EXPIRED",
                "Phone verification expired",
            )

        if verification.code_hash != self._hash_code(code):
            verification.attempt_count += 1
            if verification.attempt_count >= 5:
                verification.status = PhoneVerificationStatus.EXPIRED
            self.db.commit()
            raise _error(
                status.HTTP_400_BAD_REQUEST,
                "PHONE_VERIFICATION_CODE_MISMATCH",
                "Phone verification code mismatch",
            )

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
            raise _error(status.HTTP_409_CONFLICT, "PHONE_ALREADY_EXISTS", "Phone number already exists")

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
            raise _error(status.HTTP_409_CONFLICT, "PHONE_ALREADY_EXISTS", "Phone number already exists") from exc

        self.db.refresh(user)
        return self._build_tokens(user)

    def confirm_login(self, payload: AuthLoginConfirmRequest) -> AuthTokenResponse:
        phone = normalize_phone(payload.phone)
        self._confirm_verification(PhoneVerificationPurpose.LOGIN, phone, payload.code)

        user = self._find_user_by_phone(phone)
        if user is None:
            raise _error(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "User not found")

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
            raise _error(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Invalid token")

        user = self.db.query(User).filter(User.id == str(user_id)).first()
        if user is None:
            raise _error(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "User not found")

        access_token = create_access_token({"sub": str(user.id)})
        return AuthAccessTokenResponse(access_token=access_token, expires_in=self._access_expires_in_ms())

    def get_user_detail(self, user: User) -> UserDetailResponse:
        fresh_user = self.db.query(User).filter(User.id == str(user.id)).first()
        if fresh_user is None:
            raise _error(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "User not found")

        return UserDetailResponse(
            id=str(fresh_user.id),
            name=fresh_user.name,
            phone=fresh_user.phone,
            phone_verified_at=fresh_user.phone_verified_at,
            created_at=fresh_user.created_at,
            last_login_at=fresh_user.last_login_at,
            alarm_enabled=fresh_user.alarm_enabled,
        )

    def update_alarm(self, user: User, alarm_enabled: bool) -> None:
        fresh_user = self.db.query(User).filter(User.id == str(user.id)).first()
        if fresh_user is None:
            raise _error(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "User not found")

        fresh_user.update_alarm_setting(alarm_enabled)
        self.db.commit()

    def upsert_fcm_token(self, user: User, fcm_token: str) -> None:
        fresh_user = self.db.query(User).filter(User.id == str(user.id)).first()
        if fresh_user is None:
            raise _error(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "User not found")

        self._upsert_fcm_token(fresh_user.id, fcm_token.strip())
        self.db.commit()

    def _upsert_fcm_token(self, user_id: str, fcm_token: str) -> None:
        token = self.db.query(UserFCMToken).filter(UserFCMToken.user_id == str(user_id)).first()
        if token is None:
            token = UserFCMToken(user_id=str(user_id), fcm_token=fcm_token)
            self.db.add(token)
        else:
            token.fcm_token = fcm_token
