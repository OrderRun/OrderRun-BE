"""Phone-auth application service."""

from __future__ import annotations

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.errors import AppError, api_error
from app.core.phone import normalize_phone
from app.core.security import (
    access_token_expires_in_ms,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.core.time import utcnow_naive
from app.models.user import PhoneVerificationPurpose, User
from app.schemas.user import (
    AuthAccessTokenResponse,
    AuthLoginConfirmRequest,
    AuthLoginSendRequest,
    AuthPhoneConfirmRequest,
    AuthRefreshRequest,
    AuthSignupSendRequest,
    AuthTokenResponse,
    AuthVerificationSendResponse,
)
from app.services.phone_verification import is_login_test_code_allowed
from app.services.phone_verification_service import PhoneVerificationService
from app.services.user_profile_service import UserProfileService


class UserAuthService:
    @staticmethod
    def send_signup_verification(
        db: Session,
        phone_verification: PhoneVerificationService,
        payload: AuthSignupSendRequest,
        background_tasks: BackgroundTasks,
    ) -> AuthVerificationSendResponse:
        phone = normalize_phone(payload.phone)
        if UserAuthService._find_user_by_phone(db, phone) is not None:
            raise api_error(AppError.PHONE_ALREADY_EXISTS)
        return phone_verification.send(
            db,
            PhoneVerificationPurpose.SIGNUP,
            phone,
            background_tasks,
            name=payload.name.strip(),
            carrier=payload.carrier.strip(),
        )

    @staticmethod
    def send_login_verification(
        db: Session,
        phone_verification: PhoneVerificationService,
        payload: AuthLoginSendRequest,
        background_tasks: BackgroundTasks,
    ) -> AuthVerificationSendResponse:
        phone = normalize_phone(payload.phone)
        if UserAuthService._find_user_by_phone(db, phone) is None:
            raise api_error(AppError.INVALID_CREDENTIALS)
        return phone_verification.send(
            db,
            PhoneVerificationPurpose.LOGIN,
            phone,
            background_tasks,
        )

    @staticmethod
    def confirm_signup(
        db: Session,
        phone_verification: PhoneVerificationService,
        payload: AuthPhoneConfirmRequest,
    ) -> AuthTokenResponse:
        phone = normalize_phone(payload.phone)
        verification = phone_verification.verify(
            db,
            PhoneVerificationPurpose.SIGNUP,
            phone,
            payload.code,
        )

        if UserAuthService._find_user_by_phone(db, phone) is not None:
            db.rollback()
            raise api_error(AppError.PHONE_ALREADY_EXISTS)

        now = utcnow_naive()
        user = User(
            name=verification.name or "",
            phone=phone,
            phone_verified_at=now,
            last_login_at=now,
            alarm_enabled=False,
        )
        db.add(user)
        try:
            db.commit()
        except Exception as exc:  # pragma: no cover - defensive transactional guard
            db.rollback()
            raise api_error(AppError.PHONE_ALREADY_EXISTS) from exc

        db.refresh(user)
        return UserAuthService._build_tokens(user)

    @staticmethod
    def confirm_login(
        db: Session,
        phone_verification: PhoneVerificationService,
        payload: AuthLoginConfirmRequest,
    ) -> AuthTokenResponse:
        phone = normalize_phone(payload.phone)
        user = UserAuthService._find_user_by_phone(db, phone)
        if user is None:
            raise api_error(AppError.USER_NOT_FOUND)

        if not is_login_test_code_allowed(payload.code):
            phone_verification.verify(
                db,
                PhoneVerificationPurpose.LOGIN,
                phone,
                payload.code,
            )

        user.update_last_login_at(utcnow_naive())
        if payload.fcm_token is not None:
            UserProfileService.upsert_fcm_token(db, str(user.id), payload.fcm_token.strip())

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(user)
        return UserAuthService._build_tokens(user)

    @staticmethod
    def refresh_access_token(db: Session, payload: AuthRefreshRequest) -> AuthAccessTokenResponse:
        token_payload = verify_token(payload.refresh_token, token_type="refresh")
        user_id = token_payload.get("sub")
        if not user_id:
            raise api_error(AppError.INVALID_TOKEN)

        user = db.query(User).filter(User.id == str(user_id), User.deleted.is_(False)).first()
        if user is None:
            raise api_error(AppError.USER_NOT_FOUND)

        access_token = create_access_token({"sub": str(user.id)})
        return AuthAccessTokenResponse(access_token=access_token, expires_in=access_token_expires_in_ms())

    @staticmethod
    def _find_user_by_phone(db: Session, phone: str) -> User | None:
        return db.query(User).filter(User.phone == phone, User.deleted.is_(False)).first()

    @staticmethod
    def _build_tokens(user: User) -> AuthTokenResponse:
        return AuthTokenResponse(
            access_token=create_access_token({"sub": str(user.id)}),
            refresh_token=create_refresh_token({"sub": str(user.id)}),
            token_type="Bearer",
            expires_in=access_token_expires_in_ms(),
            user_id=str(user.id),
        )
