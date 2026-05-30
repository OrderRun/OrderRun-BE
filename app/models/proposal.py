from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Enum, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ProposalStatus(str, enum.Enum):
    """Proposal status enumeration."""
    PENDING_PAYMENT = "PENDING_PAYMENT"  # 입금 대기 (초기 상태, 공개 전)
    POSTED = "POSTED"                     # 등록됨 (입금 완료 후 공개)
    OFFERED = "OFFERED"                   # 제안 접수됨
    MATCHED = "MATCHED"                   # 매칭 완료
    CANCELLED = "CANCELLED"               # 취소됨


class Proposal(Base):
    """Proposal model representing errand requests."""

    __tablename__ = "proposals"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    orderer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(50), nullable=False)
    content = Column(String(500), nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=False)
    errand_fee = Column(Integer, nullable=False)
    status = Column(Enum(ProposalStatus), nullable=False, default=ProposalStatus.PENDING_PAYMENT)

    # Payment fields
    payment_status = Column(String(20), nullable=False, default="PENDING")  # PENDING, CONFIRMED
    payment_deadline = Column(DateTime(timezone=True), nullable=False)
    depositor_name = Column(String(50), nullable=True)
    payment_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    payment_confirmed_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    # orderer = relationship("User", back_populates="proposals")

    def __repr__(self):
        return f"<Proposal(id={self.id}, title='{self.title}', status={self.status})>"

    def can_receive_offers(self) -> bool:
        """Check if the proposal can receive new offers."""
        return self.status in [ProposalStatus.POSTED, ProposalStatus.OFFERED]

    def mark_as_offered(self):
        """Mark proposal as offered when first offer is received."""
        if self.status == ProposalStatus.POSTED:
            self.status = ProposalStatus.OFFERED

    def is_payment_pending(self) -> bool:
        """Check if payment is still pending."""
        return self.status == ProposalStatus.PENDING_PAYMENT and self.payment_status == "PENDING"

    def is_payment_expired(self) -> bool:
        """Check if payment deadline has passed."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return self.is_payment_pending() and self.payment_deadline < now

    def confirm_payment(self, admin_id: str, depositor_name: str = None):
        """Confirm payment and transition to POSTED status."""
        from datetime import datetime, timezone

        if not self.is_payment_pending():
            raise ValueError(f"Cannot confirm payment for proposal in {self.status} status")

        self.payment_status = "CONFIRMED"
        self.payment_confirmed_at = datetime.now(timezone.utc)
        self.payment_confirmed_by = admin_id
        self.status = ProposalStatus.POSTED

        if depositor_name:
            self.depositor_name = depositor_name
