from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone

from app.core.errors import AppError, error_detail


async def http_exception_handler(request: Request, exc: Exception):
    """Handle HTTPException and return custom error response."""
    from fastapi import HTTPException

    if isinstance(exc, HTTPException):
        error_detail = exc.detail if isinstance(exc.detail, dict) else {
            "code": "ERROR",
            "message": str(exc.detail),
            "details": None
        }

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": error_detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    # Default error response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "서버 내부 오류가 발생했습니다.",
                "details": str(exc),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors and return custom error response."""
    # Extract first error
    errors = exc.errors()
    if errors:
        first_error = errors[0]
        field = first_error["loc"][-1] if first_error["loc"] else "unknown"
        message = first_error["msg"]
        details = f"{field}: {message}"
    else:
        first_error = None
        field = "unknown"
        details = "Validation error"

    error = AppError.VALIDATION_ERROR
    if field == "deadline" and first_error and first_error.get("type") in {
        "datetime_from_date_parsing",
        "datetime_parsing",
        "invalid_datetime_offset",
    }:
        error = AppError.INVALID_DATE_TIME_FORMAT

    return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error": error_detail(error, details),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
