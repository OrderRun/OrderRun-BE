from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone
from pydantic import ValidationError


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
        details = "Validation error"

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "요청 값이 올바르지 않습니다.",
                "details": details,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
