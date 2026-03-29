from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class ProposalCreate(BaseModel):
    """Schema for creating a new proposal."""

    title: str = Field(..., min_length=1, max_length=50, description="제목 (1-50자)")
    content: str = Field(..., min_length=1, max_length=500, description="내용 (1-500자)")
    deadline: datetime = Field(..., description="완료 희망 시각 (미래 시각)")
    errand_fee: int = Field(..., ge=0, description="심부름비 (0 이상)", validation_alias="errandFee")

    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, v: datetime) -> datetime:
        """Validate that deadline is in the future."""
        from datetime import timezone

        now = datetime.now(timezone.utc)
        # Remove timezone info for comparison if needed
        if v.tzinfo is None:
            raise ValueError("deadline must have timezone information")

        if v <= now:
            raise ValueError("deadline must be in the future")

        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "강남역에서 커피 배달",
                "content": "스타벅스 아메리카노 아이스 2잔 부탁드립니다.",
                "deadline": "2026-03-28T15:00:00+09:00",
                "errandFee": 5000,
            }
        }
    }


class ProposalResponse(BaseModel):
    """Schema for proposal response."""

    id: int
    orderer_id: int = Field(..., serialization_alias="ordererId")
    title: str
    content: str
    deadline: datetime
    errand_fee: int = Field(..., serialization_alias="errandFee")
    status: str
    payment_status: str = Field(..., serialization_alias="paymentStatus")
    payment_deadline: datetime = Field(..., serialization_alias="paymentDeadline")
    depositor_name: Optional[str] = Field(None, serialization_alias="depositorName")
    payment_confirmed_at: Optional[datetime] = Field(None, serialization_alias="paymentConfirmedAt")
    payment_confirmed_by: Optional[int] = Field(None, serialization_alias="paymentConfirmedBy")
    created_at: datetime = Field(..., serialization_alias="createdAt")
    updated_at: datetime = Field(..., serialization_alias="updatedAt")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "ordererId": 10,
                "title": "강남역에서 커피 배달",
                "content": "스타벅스 아메리카노 아이스 2잔 부탁드립니다.",
                "deadline": "2026-03-28T15:00:00+09:00",
                "errandFee": 5000,
                "status": "POSTED",
                "paymentStatus": "CONFIRMED",
                "paymentDeadline": "2026-03-28T10:30:00+09:00",
                "depositorName": "홍길동",
                "paymentConfirmedAt": "2026-03-27T12:00:00+09:00",
                "paymentConfirmedBy": 1,
                "createdAt": "2026-03-27T10:30:00+09:00",
                "updatedAt": "2026-03-27T12:00:00+09:00",
            }
        },
    }
