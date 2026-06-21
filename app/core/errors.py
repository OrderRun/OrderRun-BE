"""Central API error catalog and HTTPException factory."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException, status


@dataclass(frozen=True)
class ApiErrorSpec:
    http_status: int
    code: str
    message: str


class AppError(str, Enum):
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_WITHDRAWAL_BLOCKED = "USER_WITHDRAWAL_BLOCKED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    REQUIRED_TERMS_INVALID = "REQUIRED_TERMS_INVALID"

    INVALID_TOKEN = "INVALID_TOKEN"
    INVALID_TOKEN_CREDENTIALS = "INVALID_TOKEN_CREDENTIALS"
    INVALID_TOKEN_TYPE = "INVALID_TOKEN_TYPE"
    MISSING_CREDENTIALS = "MISSING_CREDENTIALS"
    INVALID_AUTHENTICATION_CREDENTIALS = "INVALID_AUTHENTICATION_CREDENTIALS"

    SMS_SENDER_NOT_CONFIGURED = "SMS_SENDER_NOT_CONFIGURED"
    SMS_SEND_FAILED = "SMS_SEND_FAILED"

    PHONE_ALREADY_EXISTS = "PHONE_ALREADY_EXISTS"
    PHONE_VERIFICATION_ALREADY_SENT = "PHONE_VERIFICATION_ALREADY_SENT"
    PHONE_VERIFICATION_NOT_FOUND = "PHONE_VERIFICATION_NOT_FOUND"
    PHONE_VERIFICATION_EXPIRED = "PHONE_VERIFICATION_EXPIRED"
    PHONE_VERIFICATION_CODE_MISMATCH = "PHONE_VERIFICATION_CODE_MISMATCH"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"

    INVALID_DATE_TIME_FORMAT = "INVALID_DATE_TIME_FORMAT"
    PROPOSAL_DEADLINE_INVALID = "PROPOSAL_DEADLINE_INVALID"
    PROPOSAL_ERRAND_FEE_INVALID = "PROPOSAL_ERRAND_FEE_INVALID"
    PROPOSAL_NOT_FOUND = "PROPOSAL_NOT_FOUND"
    OFFER_PROPOSAL_NOT_FOUND = "OFFER_PROPOSAL_NOT_FOUND"
    PROPOSAL_NOT_EDITABLE = "PROPOSAL_NOT_EDITABLE"
    PROPOSAL_NOT_CANCELLABLE = "PROPOSAL_NOT_CANCELLABLE"
    PROPOSAL_NOT_OPEN = "PROPOSAL_NOT_OPEN"
    PROPOSAL_NOT_MATCHABLE = "PROPOSAL_NOT_MATCHABLE"
    PROPOSAL_NOT_UPDATABLE = "PROPOSAL_NOT_UPDATABLE"
    INVALID_STATUS = "INVALID_STATUS"
    FORBIDDEN = "FORBIDDEN"

    OFFER_NOT_FOUND = "OFFER_NOT_FOUND"
    SELF_OFFER_NOT_ALLOWED = "SELF_OFFER_NOT_ALLOWED"
    DUPLICATE_OFFER = "DUPLICATE_OFFER"
    OFFER_NOT_CANCELLABLE = "OFFER_NOT_CANCELLABLE"
    OFFER_NOT_ACCEPTABLE = "OFFER_NOT_ACCEPTABLE"
    OFFER_NOT_UPDATABLE = "OFFER_NOT_UPDATABLE"

    NOTIFICATION_NOT_FOUND = "NOTIFICATION_NOT_FOUND"


ERRORS: dict[AppError, ApiErrorSpec] = {
    AppError.USER_NOT_FOUND: ApiErrorSpec(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "User not found"),
    AppError.USER_WITHDRAWAL_BLOCKED: ApiErrorSpec(
        status.HTTP_409_CONFLICT,
        "USER_WITHDRAWAL_BLOCKED",
        "진행 중인 임무, 분쟁 또는 정산이 있어 탈퇴할 수 없습니다. 모든 절차가 완료된 후 다시 이용해주세요.",
    ),
    AppError.VALIDATION_ERROR: ApiErrorSpec(
        status.HTTP_400_BAD_REQUEST,
        "VALIDATION_ERROR",
        "요청 값이 올바르지 않습니다.",
    ),
    AppError.REQUIRED_TERMS_INVALID: ApiErrorSpec(
        status.HTTP_400_BAD_REQUEST,
        "VALIDATION_ERROR",
        "Required terms must be true",
    ),
    AppError.INVALID_TOKEN: ApiErrorSpec(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Invalid token"),
    AppError.INVALID_TOKEN_CREDENTIALS: ApiErrorSpec(
        status.HTTP_401_UNAUTHORIZED,
        "INVALID_TOKEN",
        "Could not validate credentials",
    ),
    AppError.INVALID_TOKEN_TYPE: ApiErrorSpec(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Invalid token type"),
    AppError.MISSING_CREDENTIALS: ApiErrorSpec(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Missing credentials"),
    AppError.INVALID_AUTHENTICATION_CREDENTIALS: ApiErrorSpec(
        status.HTTP_401_UNAUTHORIZED,
        "INVALID_TOKEN",
        "Invalid authentication credentials",
    ),
    AppError.SMS_SENDER_NOT_CONFIGURED: ApiErrorSpec(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "SMS_SENDER_NOT_CONFIGURED",
        "SMS sender not configured",
    ),
    AppError.SMS_SEND_FAILED: ApiErrorSpec(status.HTTP_502_BAD_GATEWAY, "SMS_SEND_FAILED", "SMS sending failed"),
    AppError.PHONE_ALREADY_EXISTS: ApiErrorSpec(
        status.HTTP_409_CONFLICT,
        "PHONE_ALREADY_EXISTS",
        "Phone number already exists",
    ),
    AppError.PHONE_VERIFICATION_ALREADY_SENT: ApiErrorSpec(
        status.HTTP_409_CONFLICT,
        "PHONE_VERIFICATION_ALREADY_SENT",
        "Verification already sent",
    ),
    AppError.PHONE_VERIFICATION_NOT_FOUND: ApiErrorSpec(
        status.HTTP_404_NOT_FOUND,
        "PHONE_VERIFICATION_NOT_FOUND",
        "Phone verification not found",
    ),
    AppError.PHONE_VERIFICATION_EXPIRED: ApiErrorSpec(
        status.HTTP_400_BAD_REQUEST,
        "PHONE_VERIFICATION_EXPIRED",
        "Phone verification expired",
    ),
    AppError.PHONE_VERIFICATION_CODE_MISMATCH: ApiErrorSpec(
        status.HTTP_400_BAD_REQUEST,
        "PHONE_VERIFICATION_CODE_MISMATCH",
        "Phone verification code mismatch",
    ),
    AppError.INVALID_CREDENTIALS: ApiErrorSpec(
        status.HTTP_401_UNAUTHORIZED,
        "INVALID_CREDENTIALS",
        "Invalid credentials",
    ),
    AppError.INVALID_DATE_TIME_FORMAT: ApiErrorSpec(
        status.HTTP_400_BAD_REQUEST,
        "INVALID_DATE_TIME_FORMAT",
        "deadline 형식이 올바르지 않습니다.",
    ),
    AppError.PROPOSAL_DEADLINE_INVALID: ApiErrorSpec(
        status.HTTP_400_BAD_REQUEST,
        "PROPOSAL_DEADLINE_INVALID",
        "마감 시각은 현재 시각보다 이후여야 합니다.",
    ),
    AppError.PROPOSAL_ERRAND_FEE_INVALID: ApiErrorSpec(
        status.HTTP_400_BAD_REQUEST,
        "PROPOSAL_ERRAND_FEE_INVALID",
        "심부름비는 1000원 이상이어야 합니다.",
    ),
    AppError.PROPOSAL_NOT_FOUND: ApiErrorSpec(
        status.HTTP_404_NOT_FOUND,
        "PROPOSAL_NOT_FOUND",
        "제안을 찾을 수 없습니다.",
    ),
    AppError.OFFER_PROPOSAL_NOT_FOUND: ApiErrorSpec(
        status.HTTP_404_NOT_FOUND,
        "PROPOSAL_NOT_FOUND",
        "요청을 찾을 수 없습니다.",
    ),
    AppError.PROPOSAL_NOT_EDITABLE: ApiErrorSpec(
        status.HTTP_409_CONFLICT,
        "PROPOSAL_NOT_EDITABLE",
        "수정할 수 없는 제안 상태입니다.",
    ),
    AppError.PROPOSAL_NOT_CANCELLABLE: ApiErrorSpec(
        status.HTTP_409_CONFLICT,
        "PROPOSAL_NOT_CANCELLABLE",
        "취소할 수 없는 제안 상태입니다.",
    ),
    AppError.PROPOSAL_NOT_OPEN: ApiErrorSpec(
        status.HTTP_409_CONFLICT,
        "PROPOSAL_NOT_OPEN",
        "제안을 받을 수 없는 요청 상태입니다.",
    ),
    AppError.PROPOSAL_NOT_MATCHABLE: ApiErrorSpec(
        status.HTTP_409_CONFLICT,
        "PROPOSAL_NOT_MATCHABLE",
        "매칭할 수 없는 요청 상태입니다.",
    ),
    AppError.PROPOSAL_NOT_UPDATABLE: ApiErrorSpec(
        status.HTTP_409_CONFLICT,
        "PROPOSAL_NOT_UPDATABLE",
        "업데이트할 수 없는 요청 상태입니다.",
    ),
    AppError.INVALID_STATUS: ApiErrorSpec(status.HTTP_400_BAD_REQUEST, "INVALID_STATUS", "입금 확인 대기 상태가 아닙니다."),
    AppError.FORBIDDEN: ApiErrorSpec(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "권한이 없습니다."),
    AppError.OFFER_NOT_FOUND: ApiErrorSpec(status.HTTP_404_NOT_FOUND, "OFFER_NOT_FOUND", "제안을 찾을 수 없습니다."),
    AppError.SELF_OFFER_NOT_ALLOWED: ApiErrorSpec(
        status.HTTP_400_BAD_REQUEST,
        "SELF_OFFER_NOT_ALLOWED",
        "오더러는 본인의 요청에 러너로 제안할 수 없습니다.",
    ),
    AppError.DUPLICATE_OFFER: ApiErrorSpec(
        status.HTTP_409_CONFLICT,
        "DUPLICATE_OFFER",
        "이미 해당 요청에 제안을 제출했습니다.",
    ),
    AppError.OFFER_NOT_CANCELLABLE: ApiErrorSpec(
        status.HTTP_409_CONFLICT,
        "OFFER_NOT_CANCELLABLE",
        "취소할 수 없는 제안 상태입니다.",
    ),
    AppError.OFFER_NOT_ACCEPTABLE: ApiErrorSpec(
        status.HTTP_409_CONFLICT,
        "OFFER_NOT_ACCEPTABLE",
        "수락할 수 없는 제안 상태입니다.",
    ),
    AppError.OFFER_NOT_UPDATABLE: ApiErrorSpec(
        status.HTTP_409_CONFLICT,
        "OFFER_NOT_UPDATABLE",
        "업데이트할 수 없는 제안 상태입니다.",
    ),
    AppError.NOTIFICATION_NOT_FOUND: ApiErrorSpec(status.HTTP_404_NOT_FOUND, "ERROR", "Notification not found"),
}


def error_detail(error: AppError, details: str | None = None) -> dict:
    spec = ERRORS[error]
    return {"code": spec.code, "message": spec.message, "details": details}


def api_error(error: AppError, details: str | None = None, headers: dict[str, str] | None = None) -> HTTPException:
    spec = ERRORS[error]
    return HTTPException(
        status_code=spec.http_status,
        detail=error_detail(error, details),
        headers=headers,
    )
