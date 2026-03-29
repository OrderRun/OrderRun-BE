from sqlalchemy import Column, BigInteger, Integer, String, Enum, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


class UserStatus(str, enum.Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class OAuthProvider(str, enum.Enum):
    """OAuth provider enumeration."""
    KAKAO = "kakao"
    APPLE = "apple"


class User(Base):
    """User model representing users in the system.

    User roles are determined by their relationships:
    - Orderer: User who creates Proposals (Proposal.orderer_id)
    - Runner: User who submits Offers (Offer.runner_id)

    A single user can be both an orderer and a runner.
    """

    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    nickname = Column(String(50), nullable=True)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    is_admin = Column(Boolean, nullable=False, default=False)
    phone_number = Column(String(20), nullable=True)

    # OAuth fields
    oauth_provider = Column(Enum(OAuthProvider), nullable=False)
    oauth_id = Column(String(255), nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Unique constraint: one OAuth account per provider
    __table_args__ = (
        UniqueConstraint('oauth_provider', 'oauth_id', name='uq_oauth_provider_id'),
    )

    # Relationships
    device_tokens = relationship("DeviceToken", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_preference = relationship("NotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', provider={self.oauth_provider})>"
