"""Terms agreement persistence model."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Index, String

from app.core.time import utcnow_naive
from app.core.database import Base


class TermsType(str, enum.Enum):
    TERMS_OF_SERVICE = ("termsOfService", True)
    PRIVACY_POLICY = ("privacyPolicy", True)
    PAYMENT_REFUND_POLICY = ("paymentRefundPolicy", True)

    def __new__(cls, field_name: str, required: bool):
        value = field_name
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.field_name = field_name
        obj.required = required
        return obj


class TermsAgreement(Base):
    """Latest required terms agreement state per user."""

    __tablename__ = "terms_agreements"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, unique=True, index=True)
    terms_of_service = Column(Boolean, nullable=False)
    privacy_policy = Column(Boolean, nullable=False)
    payment_refund_policy = Column(Boolean, nullable=False)
    agreed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow_naive, onupdate=utcnow_naive)

    __table_args__ = (
        Index("idx_terms_agreements_user_id", "user_id"),
    )


__all__ = ["TermsAgreement", "TermsType"]
