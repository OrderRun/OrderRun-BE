"""JWT helpers and current-user dependency."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import AppError, api_error
from app.models.user import User


security = HTTPBearer(auto_error=False)


def _token_error(error: AppError = AppError.INVALID_TOKEN):
    return api_error(error, headers={"WWW-Authenticate": "Bearer"})


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload.update({"exp": expire, "type": "access"})
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: Dict[str, Any]) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload.update({"exp": expire, "type": "refresh"})
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise _token_error(AppError.INVALID_TOKEN_CREDENTIALS) from exc

    if payload.get("type") != token_type:
        raise _token_error(AppError.INVALID_TOKEN_TYPE)

    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise _token_error(AppError.MISSING_CREDENTIALS)

    payload = verify_token(credentials.credentials, token_type="access")
    user_id = payload.get("sub")
    if not user_id:
        raise _token_error(AppError.INVALID_AUTHENTICATION_CREDENTIALS)

    user = db.query(User).filter(User.id == str(user_id), User.deleted.is_(False)).first()
    if user is None:
        raise api_error(AppError.USER_NOT_FOUND)

    return user
