"""
Notification and Device Token models for push notification system.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, Integer, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class DevicePlatform(str, enum.Enum):
    """Device platform types for push notifications."""
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class NotificationType(str, enum.Enum):
    """Types of notifications that can be sent."""
    PROPOSAL_NEW = "proposal_new"  # New proposal created
    PROPOSAL_MATCHED = "proposal_matched"  # Proposal matched with an offer
    PROPOSAL_CANCELLED = "proposal_cancelled"  # Proposal cancelled
    OFFER_NEW = "offer_new"  # New offer received on your proposal
    OFFER_ACCEPTED = "offer_accepted"  # Your offer was accepted
    OFFER_REJECTED = "offer_rejected"  # Your offer was rejected
    MISSION_STARTED = "mission_started"  # Mission started
    MISSION_COMPLETED = "mission_completed"  # Mission completed
    PAYMENT_COMPLETED = "payment_completed"  # Payment completed
    PAYMENT_FAILED = "payment_failed"  # Payment failed
    SYSTEM_ANNOUNCEMENT = "system_announcement"  # System-wide announcement
    CUSTOM = "custom"  # Custom notification


class NotificationStatus(str, enum.Enum):
    """Status of notification delivery."""
    PENDING = "pending"  # Queued for sending
    SENT = "sent"  # Successfully sent to FCM
    DELIVERED = "delivered"  # Delivered to device
    FAILED = "failed"  # Failed to send
    READ = "read"  # User has read the notification


class DeviceToken(Base):
    """
    Device token for FCM push notifications.

    Each user can have multiple devices registered for notifications.
    """
    __tablename__ = "device_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    platform: Mapped[DevicePlatform] = mapped_column(
        Enum(DevicePlatform),
        nullable=False
    )
    device_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Optional device identifier
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="device_tokens")

    def __repr__(self) -> str:
        return f"<DeviceToken(id={self.id}, user_id={self.user_id}, platform={self.platform})>"


class Notification(Base):
    """
    Notification record for tracking sent push notifications.

    Stores notification content, delivery status, and metadata.
    """
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional payload data (JSON string)
    data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Related entity IDs (optional, for linking to proposals, offers, missions, etc.)
    related_entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    related_entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Delivery tracking
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus),
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True
    )
    fcm_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # FCM response message ID
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.notification_type}, status={self.status})>"


class NotificationPreference(Base):
    """
    User preferences for notification settings.

    Controls which types of notifications a user wants to receive.
    """
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Notification type preferences
    enable_proposal_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_offer_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_mission_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_payment_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_system_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Quiet hours (optional - future feature)
    enable_quiet_hours: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quiet_hours_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Hour 0-23
    quiet_hours_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Hour 0-23

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notification_preference")

    def __repr__(self) -> str:
        return f"<NotificationPreference(id={self.id}, user_id={self.user_id})>"
