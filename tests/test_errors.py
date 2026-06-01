from __future__ import annotations

from fastapi import status

from app.core.errors import ERRORS, AppError, api_error, error_detail


def test_error_catalog_has_required_fields_for_every_error():
    assert set(ERRORS) == set(AppError)
    for spec in ERRORS.values():
        assert spec.http_status >= 400
        assert spec.code
        assert spec.message


def test_api_error_builds_standard_http_exception_detail():
    exc = api_error(AppError.SMS_SEND_FAILED)

    assert exc.status_code == status.HTTP_502_BAD_GATEWAY
    assert exc.detail == {
        "code": "SMS_SEND_FAILED",
        "message": "SMS sending failed",
        "details": None,
    }


def test_api_error_preserves_details_and_headers():
    exc = api_error(
        AppError.INVALID_TOKEN_CREDENTIALS,
        details="token: invalid signature",
        headers={"WWW-Authenticate": "Bearer"},
    )

    assert exc.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.headers == {"WWW-Authenticate": "Bearer"}
    assert exc.detail == {
        "code": "INVALID_TOKEN",
        "message": "Could not validate credentials",
        "details": "token: invalid signature",
    }


def test_error_detail_uses_validation_catalog_message():
    assert error_detail(AppError.VALIDATION_ERROR, "field: error") == {
        "code": "VALIDATION_ERROR",
        "message": "요청 값이 올바르지 않습니다.",
        "details": "field: error",
    }
