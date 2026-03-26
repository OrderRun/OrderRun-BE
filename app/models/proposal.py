from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Enum, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ProposalStatus(str, enum.Enum):
    """Proposal status enumeration."""
    POSTED = "POSTED"       # 등록됨 (초기 상태)
    OFFERED = "OFFERED"     # 제안 접수됨
    MATCHED = "MATCHED"     # 매칭 완료
    CANCELLED = "CANCELLED" # 취소됨


class Proposal(Base):
    """Proposal model representing errand requests."""

    __tablename__ = "proposals"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    orderer_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(50), nullable=False)
    content = Column(String(500), nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=False)
    errand_fee = Column(Integer, nullable=False)
    status = Column(Enum(ProposalStatus), nullable=False, default=ProposalStatus.POSTED)

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
