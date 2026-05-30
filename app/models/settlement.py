"""Settlement account persistence model."""

from __future__ import annotations

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

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
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", name="uk_settlement_accounts_user_id"),)
