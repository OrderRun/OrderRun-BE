"""Account and phone-auth persistence models."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class PhoneVerificationPurpose(str, enum.Enum):
    SIGNUP = "SIGNUP"
    LOGIN = "LOGIN"


class PhoneVerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    EXPIRED = "EXPIRED"


class User(Base):
    """User account model for phone-auth based access."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    password_hash = Column(String(255), nullable=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    phone_verified_at = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    alarm_enabled = Column(Boolean, nullable=False, default=False, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    device_tokens = relationship("DeviceToken", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_preference = relationship(
        "NotificationPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def update_last_login_at(self, current_time: datetime) -> None:
        self.last_login_at = current_time

    def update_alarm_setting(self, alarm_enabled: bool) -> None:
        self.alarm_enabled = alarm_enabled

    def verify_phone(self, phone: str, verified_at: datetime) -> None:
        self.phone = phone
        self.phone_verified_at = verified_at


class AuthPhoneVerification(Base):
    """Phone verification records for signup and login flows."""

    __tablename__ = "auth_phone_verifications"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    purpose = Column(Enum(PhoneVerificationPurpose), nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)
    name = Column(String(100), nullable=True)
    carrier = Column(String(50), nullable=True)
    code_hash = Column(String(100), nullable=False)
    status = Column(Enum(PhoneVerificationStatus), nullable=False, default=PhoneVerificationStatus.PENDING)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_auth_phone_verifications_purpose_phone_status_expires_at", "purpose", "phone", "status", "expires_at"),
        Index("idx_auth_phone_verifications_purpose_phone_status", "purpose", "phone", "status"),
    )


class UserFCMToken(Base):
    """Single FCM token record per user."""

    __tablename__ = "user_fcm_tokens"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, unique=True, index=True)
    fcm_token = Column(String(4096), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

__all__ = [
    "AuthPhoneVerification",
    "PhoneVerificationPurpose",
    "PhoneVerificationStatus",
    "User",
    "UserFCMToken",
]
