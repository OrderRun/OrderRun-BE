from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional
from datetime import datetime, timezone

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail schema."""

    code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    details: Optional[str] = Field(None, description="상세 정보")


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""

    success: bool = Field(..., description="성공 여부")
    data: Optional[T] = Field(None, description="응답 데이터")
    message: Optional[str] = Field(None, description="응답 메시지")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "data": {"id": 1, "name": "example"},
                "message": "Success",
            }
        }
    }


class PageResponse(BaseModel, Generic[T]):
    """Generic paginated response payload."""

    items: list[T] = Field(..., description="현재 페이지 항목")
    page: int = Field(..., description="현재 페이지 번호")
    size: int = Field(..., description="페이지 크기")
    total: int = Field(..., description="전체 항목 수")


class ErrorResponse(BaseModel):
    """Error response schema."""

    success: bool = Field(False, description="성공 여부 (항상 false)")
    error: ErrorDetail = Field(..., description="에러 상세 정보")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="에러 발생 시각")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "요청 값이 올바르지 않습니다.",
                    "details": "title: 제목은 50자를 초과할 수 없습니다",
                },
                "timestamp": "2026-03-27T12:00:00+09:00",
            }
        }
    }
