"""
Email log model for tracking email send history.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Enum, Integer, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.core.database import Base


class EmailStatus(str, enum.Enum):
    """Status of email delivery."""
    PENDING = "pending"  # Queued for sending
    SENT = "sent"  # Successfully sent via SMTP
    FAILED = "failed"  # Failed to send
    BOUNCED = "bounced"  # Email bounced back
    DELIVERED = "delivered"  # Confirmed delivered (if tracking enabled)


class EmailLog(Base):
    """
    Email send log for tracking all emails sent through the system.

    This model stores the history of all emails sent, including:
    - Recipient information
    - Email content metadata
    - Send status and timestamps
    - Error information for failed sends
    """
    __tablename__ = "email_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Recipient information
    to_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    to_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Sender information (can override default)
    from_email: Mapped[str] = mapped_column(String(255), nullable=False)
    from_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Email content
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Plain text version
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # HTML version

    # Template information (if using templates)
    template_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Optional user association
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
        comment="Optional user ID if email is sent to a registered user"
    )

    # Send status
    status: Mapped[EmailStatus] = mapped_column(
        Enum(EmailStatus),
        default=EmailStatus.PENDING,
        nullable=False,
        index=True
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Additional metadata (JSON string)
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<EmailLog(id={self.id}, to={self.to_email}, status={self.status})>"
