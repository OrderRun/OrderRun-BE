"""Settlement account API schemas."""

from __future__ import annotations

from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SettlementAccountRequest(BaseModel):
    bank_code: str = Field(..., alias="bankCode")
    bank_name: str = Field(..., alias="bankName", max_length=50)
    account_number: str = Field(..., alias="accountNumber")
    account_holder: str = Field(..., alias="accountHolder", max_length=100)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("bank_code")
    @classmethod
    def validate_bank_code(cls, value: str) -> str:
        stripped = value.strip()
        if not re.fullmatch(r"\d{2,10}", stripped):
            raise ValueError("bankCode must be 2 to 10 digits")
        return stripped

    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, value: str) -> str:
        stripped = value.strip()
        if not re.fullmatch(r"\d{6,30}", stripped):
            raise ValueError("accountNumber must be 6 to 30 digits")
        return stripped

    @field_validator("bank_name", "account_holder")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class SettlementAccountResponse(BaseModel):
    bank_code: str = Field(..., alias="bankCode")
    bank_name: str = Field(..., alias="bankName")
    masked_account_number: str = Field(..., alias="maskedAccountNumber")
    account_holder: str = Field(..., alias="accountHolder")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
