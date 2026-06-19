"""Settlement account API schemas."""

from __future__ import annotations

from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


SUPPORTED_BANK_NAMES = (
    "국민은행",
    "신한은행",
    "우리은행",
    "하나은행",
    "농협은행",
    "기업은행",
    "카카오뱅크",
    "토스뱅크",
    "케이뱅크",
    "SC제일은행",
    "한국씨티은행",
    "산업은행",
    "수협은행",
    "대구은행",
    "부산은행",
    "광주은행",
    "제주은행",
    "전북은행",
    "경남은행",
    "새마을금고",
    "신협",
    "우체국",
)


class SettlementAccountRequest(BaseModel):
    bank_name: str = Field(..., alias="bankName", max_length=50)
    account_number: str = Field(..., alias="accountNumber")
    account_holder: str = Field(..., alias="accountHolder", max_length=100)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, value: str) -> str:
        stripped = value.strip()
        if not re.fullmatch(r"\d{6,30}", stripped):
            raise ValueError("accountNumber must be 6 to 30 digits")
        return stripped

    @field_validator("bank_name")
    @classmethod
    def validate_bank_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        if stripped not in SUPPORTED_BANK_NAMES:
            raise ValueError("unsupported bankName")
        return stripped

    @field_validator("account_holder")
    @classmethod
    def validate_account_holder(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class SettlementAccountResponse(BaseModel):
    bank_name: str = Field(..., alias="bankName")
    account_holder: str = Field(..., alias="accountHolder")
    masked_account_number: str = Field(..., alias="maskedAccountNumber")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class SettlementBankNamesResponse(BaseModel):
    bank_names: list[str] = Field(..., alias="bankNames")

    model_config = ConfigDict(populate_by_name=True)
