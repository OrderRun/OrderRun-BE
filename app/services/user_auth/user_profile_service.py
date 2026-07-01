"""User profile application service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import AppError, api_error
from app.models.user import User, UserFCMToken
from app.schemas.user import UserDetailResponse


class UserProfileService:
    @staticmethod
    def get_user_detail(db: Session, user: User) -> UserDetailResponse:
        fresh_user = UserProfileService._get_active_user(db, str(user.id))
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

    @staticmethod
    def update_alarm(db: Session, user: User, alarm_enabled: bool) -> None:
        fresh_user = UserProfileService._get_active_user(db, str(user.id))
        fresh_user.update_alarm_setting(alarm_enabled)
        db.commit()

    @staticmethod
    def update_name(db: Session, user: User, name: str) -> None:
        fresh_user = UserProfileService._get_active_user(db, str(user.id))
        fresh_user.update_name(name.strip())
        db.commit()

    @staticmethod
    def update_fcm_token(db: Session, user: User, fcm_token: str) -> None:
        fresh_user = UserProfileService._get_active_user(db, str(user.id))
        UserProfileService.upsert_fcm_token(db, str(fresh_user.id), fcm_token.strip())
        db.commit()

    @staticmethod
    def upsert_fcm_token(db: Session, user_id: str, fcm_token: str) -> None:
        """Upsert without committing so an orchestrating use case owns the transaction."""
        token = db.query(UserFCMToken).filter(UserFCMToken.user_id == str(user_id)).first()
        if token is None:
            db.add(UserFCMToken(user_id=str(user_id), fcm_token=fcm_token))
        else:
            token.fcm_token = fcm_token

    @staticmethod
    def _get_active_user(db: Session, user_id: str) -> User:
        user = db.query(User).filter(User.id == user_id, User.deleted.is_(False)).first()
        if user is None:
            raise api_error(AppError.USER_NOT_FOUND)
        return user
