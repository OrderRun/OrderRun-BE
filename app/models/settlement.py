"""Settlement account persistence model."""

from __future__ import annotations

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, UniqueConstraint

from app.core.time import utcnow_naive
from app.core.database import Base


class SettlementAccount(Base):
    """Bank account used for runner settlement payouts."""

    __tablename__ = "settlement_accounts"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, unique=True, index=True)
    bank_code = Column(String(10), nullable=False)
    bank_name = Column(String(50), nullable=False)
    account_holder = Column(String(100), nullable=False)
    encrypted_account_number = Column(String(500), nullable=False)
    masked_account_number = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive, onupdate=utcnow_naive)

    __table_args__ = (UniqueConstraint("user_id", name="uk_settlement_accounts_user_id"),)
