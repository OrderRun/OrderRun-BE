"""Mission model representing the execution contract."""
from sqlalchemy import Column, BigInteger, Integer, String, Text, Enum, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class MissionStatus(str, enum.Enum):
    """Mission status enumeration."""
    CREATED = "CREATED"                      # 매칭 (미션 생성)
    IN_PROGRESS = "IN_PROGRESS"              # 배달 중
    DELIVERY_COMPLETED = "DELIVERY_COMPLETED"  # 전달 완료
    RECEIVED_CONFIRMED = "RECEIVED_CONFIRMED"  # 수령 확인
    SETTLED = "SETTLED"                      # 정산 완료
    DISPUTED = "DISPUTED"                    # 분쟁
    REFUNDED = "REFUNDED"                    # 환불


class Mission(Base):
    """Mission model representing the execution contract between orderer and runner."""

    __tablename__ = "missions"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proposal_id = Column(BigInteger, ForeignKey("proposals.id"), nullable=False, index=True)
    offer_id = Column(BigInteger, ForeignKey("offers.id"), nullable=False, unique=True)
    orderer_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    runner_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)

    # Contract amount snapshot (immutable after creation)
    contract_amount = Column(Integer, nullable=False)

    # Mission status
    status = Column(Enum(MissionStatus), nullable=False, default=MissionStatus.CREATED, index=True)

    # Delivery proof
    delivery_proof_image_url = Column(String(500), nullable=True)

    # Dispute information
    dispute_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    settled_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Mission(id={self.id}, proposal_id={self.proposal_id}, status={self.status})>"

    def can_start(self) -> bool:
        """Check if the mission can be started."""
        return self.status == MissionStatus.CREATED

    def start_delivery(self):
        """Start the delivery."""
        from datetime import datetime, timezone

        if not self.can_start():
            raise ValueError("Cannot start mission that is not in CREATED status")

        self.status = MissionStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)

    def can_complete_delivery(self) -> bool:
        """Check if delivery can be completed."""
        return self.status == MissionStatus.IN_PROGRESS

    def complete_delivery(self, proof_image_url: str):
        """Complete the delivery with proof image."""
        from datetime import datetime, timezone

        if not self.can_complete_delivery():
            raise ValueError("Cannot complete delivery for mission not in IN_PROGRESS status")

        self.status = MissionStatus.DELIVERY_COMPLETED
        self.delivery_proof_image_url = proof_image_url
        self.completed_at = datetime.now(timezone.utc)

    def can_confirm_receipt(self) -> bool:
        """Check if receipt can be confirmed."""
        return self.status == MissionStatus.DELIVERY_COMPLETED

    def confirm_receipt(self):
        """Confirm receipt by orderer."""
        if not self.can_confirm_receipt():
            raise ValueError("Cannot confirm receipt for mission not in DELIVERY_COMPLETED status")

        self.status = MissionStatus.RECEIVED_CONFIRMED

    def can_settle(self) -> bool:
        """Check if mission can be settled."""
        return self.status == MissionStatus.RECEIVED_CONFIRMED

    def settle(self):
        """Settle the mission (transfer payment to runner)."""
        from datetime import datetime, timezone

        if not self.can_settle():
            raise ValueError("Cannot settle mission that is not in RECEIVED_CONFIRMED status")

        self.status = MissionStatus.SETTLED
        self.settled_at = datetime.now(timezone.utc)

    def can_raise_dispute(self) -> bool:
        """Check if dispute can be raised."""
        # Dispute can be raised from DELIVERY_COMPLETED until before SETTLED
        return self.status in [
            MissionStatus.DELIVERY_COMPLETED,
            MissionStatus.RECEIVED_CONFIRMED
        ]

    def raise_dispute(self, reason: str):
        """Raise a dispute."""
        if not self.can_raise_dispute():
            raise ValueError("Cannot raise dispute at this stage")

        self.status = MissionStatus.DISPUTED
        self.dispute_reason = reason

    def can_refund(self) -> bool:
        """Check if mission can be refunded."""
        return self.status == MissionStatus.DISPUTED

    def refund(self):
        """Process refund."""
        if not self.can_refund():
            raise ValueError("Cannot refund mission that is not in DISPUTED status")

        self.status = MissionStatus.REFUNDED
