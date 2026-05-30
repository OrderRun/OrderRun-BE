"""Schemas for terms agreement endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TermsAgreementRequest(BaseModel):
    terms_of_service: bool = Field(..., alias="termsOfService")
    privacy_policy: bool = Field(..., alias="privacyPolicy")
    payment_refund_policy: bool = Field(..., alias="paymentRefundPolicy")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("terms_of_service", "privacy_policy", "payment_refund_policy")
    @classmethod
    def required_terms_must_be_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("required terms must be true")
        return value


class TermsAgreementResponse(BaseModel):
    user_id: str = Field(..., alias="userId")
    terms_of_service: bool = Field(..., alias="termsOfService")
    privacy_policy: bool = Field(..., alias="privacyPolicy")
    payment_refund_policy: bool = Field(..., alias="paymentRefundPolicy")
    agreed_at: datetime = Field(..., alias="agreedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
