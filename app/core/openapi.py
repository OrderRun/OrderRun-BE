"""OpenAPI response example helpers."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.core.errors import AppError, ERRORS
from app.schemas.common import ErrorResponse


EXAMPLE_TIMESTAMP = "2026-06-01T12:00:00+09:00"


def error_response_example(error: AppError, details: str | None = None) -> dict[str, Any]:
    spec = ERRORS[error]
    return {
        "success": False,
        "error": {
            "code": spec.code,
            "message": spec.message,
            "details": details,
        },
        "timestamp": EXAMPLE_TIMESTAMP,
    }


def error_responses(*errors: AppError) -> dict[int | str, dict[str, Any]]:
    grouped: dict[int, list[AppError]] = defaultdict(list)
    for error in errors:
        grouped[ERRORS[error].http_status].append(error)

    responses: dict[int | str, dict[str, Any]] = {}
    for http_status, status_errors in grouped.items():
        responses[http_status] = {
            "model": ErrorResponse,
            "description": "실패 응답",
            "content": {
                "application/json": {
                    "examples": {
                        error.value: {
                            "summary": ERRORS[error].code,
                            "value": error_response_example(error),
                        }
                        for error in status_errors
                    }
                }
            },
        }

    return responses


def success_response(example: dict[str, Any], description: str = "성공 응답") -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "example": example,
            }
        },
    }


VALIDATION_ERROR_RESPONSE = error_responses(AppError.VALIDATION_ERROR)
AUTH_ERROR_RESPONSES = error_responses(AppError.INVALID_TOKEN)
