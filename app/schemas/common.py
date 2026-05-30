from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional
from datetime import datetime, timezone
from math import ceil

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

    content: list[T] = Field(..., description="현재 페이지 항목")
    total_elements: int = Field(..., serialization_alias="totalElements", description="전체 항목 수")
    total_pages: int = Field(..., serialization_alias="totalPages", description="전체 페이지 수")
    page_number: int = Field(..., serialization_alias="pageNumber", description="현재 페이지 번호")
    page_size: int = Field(..., serialization_alias="pageSize", description="페이지 크기")
    first: bool = Field(..., description="첫 페이지 여부")
    last: bool = Field(..., description="마지막 페이지 여부")

    @classmethod
    def of(cls, content: list[T], page_number: int, page_size: int, total_elements: int) -> "PageResponse[T]":
        total_pages = ceil(total_elements / page_size) if page_size > 0 and total_elements > 0 else 0
        return cls(
            content=content,
            total_elements=total_elements,
            total_pages=total_pages,
            page_number=page_number,
            page_size=page_size,
            first=page_number <= 0,
            last=total_pages == 0 or page_number >= total_pages - 1,
        )


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
