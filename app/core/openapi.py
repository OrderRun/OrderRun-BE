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
    expanded_errors = list(errors)
    if AppError.INVALID_TOKEN in expanded_errors:
        for auth_error in (
            AppError.MISSING_CREDENTIALS,
            AppError.INVALID_TOKEN_CREDENTIALS,
            AppError.INVALID_TOKEN_TYPE,
            AppError.INVALID_AUTHENTICATION_CREDENTIALS,
        ):
            if auth_error not in expanded_errors:
                expanded_errors.append(auth_error)

    grouped: dict[int, list[AppError]] = defaultdict(list)
    for error in expanded_errors:
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


def success_response_examples(examples: dict[str, dict[str, Any]], description: str = "성공 응답") -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "examples": {
                    key: {
                        "summary": key,
                        "value": value,
                    }
                    for key, value in examples.items()
                }
            }
        },
    }


def no_content_response(description: str = "성공 응답") -> dict[str, Any]:
    return {"description": description}


VALIDATION_ERROR_RESPONSE = error_responses(AppError.VALIDATION_ERROR)
AUTH_ERROR_RESPONSES = error_responses(AppError.INVALID_TOKEN)

EXAMPLE_USER_ID = "550e8400-e29b-41d4-a716-446655440000"
EXAMPLE_RUNNER_ID = "550e8400-e29b-41d4-a716-446655440001"
EXAMPLE_CREATED_AT = "2026-06-01T12:00:00+09:00"
EXAMPLE_UPDATED_AT = "2026-06-01T12:10:00+09:00"
EXAMPLE_DEADLINE = "2026-06-02T12:00:00+09:00"

USER_DETAIL_EXAMPLE = {
    "success": True,
    "data": {
        "id": EXAMPLE_USER_ID,
        "name": "홍길동",
        "phone": "01012345678",
        "phoneVerifiedAt": EXAMPLE_CREATED_AT,
        "createdAt": EXAMPLE_CREATED_AT,
        "lastLoginAt": EXAMPLE_UPDATED_AT,
        "alarmEnabled": False,
    },
}
USER_ALARM_EXAMPLE = {"success": True, "data": None, "message": "알람 설정이 업데이트되었습니다."}
USER_FCM_TOKEN_EXAMPLE = {"success": True, "data": None, "message": "FCM 토큰이 업데이트되었습니다."}

TERMS_AGREEMENT_EXAMPLE = {
    "success": True,
    "data": {
        "userId": EXAMPLE_USER_ID,
        "termsOfService": True,
        "privacyPolicy": True,
        "paymentRefundPolicy": True,
        "agreedAt": EXAMPLE_CREATED_AT,
    },
    "message": "약관 동의가 완료되었습니다.",
}

PROPOSAL_EXAMPLE = {
    "id": 1,
    "title": "강남역 커피 배달",
    "content": "스타벅스 아메리카노 아이스 2잔 부탁드립니다.",
    "deadline": EXAMPLE_DEADLINE,
    "errandFee": 5000,
    "status": "POSTED",
}
PROPOSAL_STATE_TIMESTAMPS = {
    "matchedAt": None,
    "deliveryReportedAt": None,
    "receivedConfirmedAt": None,
    "settledAt": None,
    "disputedAt": None,
    "refundedAt": None,
    "offers": [],
}
PROPOSAL_DETAIL_EXAMPLE = {**PROPOSAL_EXAMPLE, **PROPOSAL_STATE_TIMESTAMPS}
PROPOSAL_MATCHED_DETAIL_EXAMPLE = {
    **PROPOSAL_EXAMPLE,
    **PROPOSAL_STATE_TIMESTAMPS,
    "status": "MATCHED",
    "matchedAt": EXAMPLE_UPDATED_AT,
}
PROPOSAL_HOLDING_EXAMPLE = {**PROPOSAL_EXAMPLE, "status": "HOLDING"}
PROPOSAL_CANCELLED_EXAMPLE = {**PROPOSAL_EXAMPLE, "status": "CANCELLED"}
PROPOSAL_PAGE_EXAMPLE = {
    "success": True,
    "data": {
        "content": [PROPOSAL_EXAMPLE],
        "totalElements": 1,
        "totalPages": 1,
        "pageNumber": 0,
        "pageSize": 20,
        "first": True,
        "last": True,
    },
    "message": None,
}
PROPOSAL_OWN_EXAMPLE = {
    **PROPOSAL_EXAMPLE,
    "ordererId": EXAMPLE_USER_ID,
    "offerCount": 1,
    "offers": [
        {
            "id": 10,
            "proposalId": 1,
            "runnerId": EXAMPLE_RUNNER_ID,
            "status": "WAITING",
            "createdAt": EXAMPLE_CREATED_AT,
        }
    ],
    "createdAt": EXAMPLE_CREATED_AT,
    "updatedAt": EXAMPLE_UPDATED_AT,
}
PROPOSAL_OWN_PAGE_EXAMPLE = {
    "success": True,
    "data": {
        "content": [PROPOSAL_OWN_EXAMPLE],
        "totalElements": 1,
        "totalPages": 1,
        "pageNumber": 0,
        "pageSize": 20,
        "first": True,
        "last": True,
    },
    "message": None,
}
PROPOSAL_CREATE_EXAMPLE = {
    "success": True,
    "data": PROPOSAL_HOLDING_EXAMPLE,
    "message": "요청이 등록되었습니다.",
}
PROPOSAL_UPDATE_EXAMPLE = {
    "success": True,
    "data": {**PROPOSAL_HOLDING_EXAMPLE, "title": "수정된 제목"},
    "message": "제안이 수정되었습니다.",
}
PROPOSAL_CANCEL_EXAMPLE = {
    "success": True,
    "data": PROPOSAL_CANCELLED_EXAMPLE,
    "message": "제안이 취소되었습니다.",
}
PROPOSAL_RECEIVED_EXAMPLE = {
    "success": True,
    "data": {
        **PROPOSAL_MATCHED_DETAIL_EXAMPLE,
        "status": "COMPLETED",
        "receivedConfirmedAt": EXAMPLE_UPDATED_AT,
    },
    "message": "완료 확인되었습니다.",
}
PROPOSAL_DISPUTE_EXAMPLE = {
    "success": True,
    "data": {**PROPOSAL_MATCHED_DETAIL_EXAMPLE, "status": "DISPUTED", "disputedAt": EXAMPLE_UPDATED_AT},
    "message": "분쟁이 접수되었습니다.",
}

OFFER_EXAMPLE = {
    "id": 10,
    "proposalId": 1,
    "runnerId": EXAMPLE_RUNNER_ID,
    "runnerName": "Runner One",
    "status": "WAITING",
    "acceptedAt": None,
    "deliveryCompletedAt": None,
    "receiptConfirmedAt": None,
    "settledAt": None,
    "disputedAt": None,
    "refundedAt": None,
    "createdAt": EXAMPLE_CREATED_AT,
}
OFFER_PAGE_EXAMPLE = {
    "success": True,
    "data": {
        "content": [OFFER_EXAMPLE],
        "totalElements": 1,
        "totalPages": 1,
        "pageNumber": 0,
        "pageSize": 20,
        "first": True,
        "last": True,
    },
    "message": "Success",
}
OFFER_LIST_EXAMPLE = {"success": True, "data": [OFFER_EXAMPLE], "message": "Success"}
OFFER_CREATE_EXAMPLE = {"success": True, "data": OFFER_EXAMPLE, "message": "제안이 제출되었습니다."}
OFFER_DETAIL_EXAMPLE = {"success": True, "data": OFFER_EXAMPLE, "message": "Success"}
OFFER_ACCEPTED_DETAIL_EXAMPLE = {
    "success": True,
    "data": {**OFFER_EXAMPLE, "status": "ACCEPTED", "acceptedAt": EXAMPLE_UPDATED_AT},
    "message": "Success",
}
OFFER_DELIVERY_EXAMPLE = {
    "success": True,
    "data": {
        **OFFER_EXAMPLE,
        "status": "COMPLETED",
        "acceptedAt": EXAMPLE_CREATED_AT,
        "deliveryCompletedAt": EXAMPLE_UPDATED_AT,
    },
    "message": "완료 처리되었습니다.",
}
OFFER_DISPUTE_EXAMPLE = {
    "success": True,
    "data": {**OFFER_EXAMPLE, "status": "DISPUTED", "acceptedAt": EXAMPLE_CREATED_AT, "disputedAt": EXAMPLE_UPDATED_AT},
    "message": "분쟁이 접수되었습니다.",
}
OFFER_ACCEPT_EXAMPLE = {
    "success": True,
    "data": {
        "proposalId": 1,
        "offerId": 10,
        "proposalStatus": "MATCHED",
        "acceptedOfferStatus": "ACCEPTED",
        "rejectedOfferCount": 1,
        "ordererId": EXAMPLE_USER_ID,
        "runnerId": EXAMPLE_RUNNER_ID,
        "acceptedAt": EXAMPLE_CREATED_AT,
    },
    "message": "제안이 수락되었습니다.",
}

OFFER_SETTLED_EXAMPLE = {
    "success": True,
    "data": {
        **OFFER_EXAMPLE,
        "status": "SETTLED",
        "acceptedAt": EXAMPLE_CREATED_AT,
        "deliveryCompletedAt": EXAMPLE_UPDATED_AT,
        "receiptConfirmedAt": EXAMPLE_UPDATED_AT,
        "settledAt": EXAMPLE_UPDATED_AT,
    },
    "message": "제안 정산이 완료되었습니다.",
}
OFFER_REFUNDED_EXAMPLE = {
    "success": True,
    "data": {**OFFER_EXAMPLE, "status": "REFUNDED", "acceptedAt": EXAMPLE_CREATED_AT, "disputedAt": EXAMPLE_UPDATED_AT, "refundedAt": EXAMPLE_UPDATED_AT},
    "message": "제안 환불이 완료되었습니다.",
}

SETTLEMENT_ACCOUNT_EXAMPLE = {
    "bankCode": "004",
    "bankName": "국민은행",
    "maskedAccountNumber": "********9012",
    "accountHolder": "홍길동",
    "updatedAt": EXAMPLE_UPDATED_AT,
}
SETTLEMENT_ACCOUNT_GET_EXAMPLE = {"success": True, "data": SETTLEMENT_ACCOUNT_EXAMPLE, "message": "Success"}
SETTLEMENT_ACCOUNT_EMPTY_EXAMPLE = {"success": True, "data": None, "message": "Success"}
SETTLEMENT_ACCOUNT_SAVE_EXAMPLE = {
    "success": True,
    "data": SETTLEMENT_ACCOUNT_EXAMPLE,
    "message": "정산 계좌가 저장되었습니다.",
}

NOTIFICATION_EXAMPLE = {
    "id": 1,
    "user_id": EXAMPLE_USER_ID,
    "notification_type": "custom",
    "title": "테스트 알림",
    "body": "테스트 알림 본문입니다.",
    "data": "{\"proposalId\":1}",
    "related_entity_type": "proposal",
    "related_entity_id": 1,
    "status": "sent",
    "fcm_message_id": "projects/orderrun/messages/1",
    "error_message": "No FCM token",
    "created_at": EXAMPLE_CREATED_AT,
    "sent_at": EXAMPLE_CREATED_AT,
    "delivered_at": EXAMPLE_UPDATED_AT,
    "read_at": EXAMPLE_UPDATED_AT,
}
NOTIFICATION_LIST_EXAMPLE = {
    "total": 1,
    "notifications": [NOTIFICATION_EXAMPLE],
    "page": 1,
    "page_size": 20,
}
NOTIFICATION_STATS_EXAMPLE = {
    "total_notifications": 3,
    "unread_count": 1,
    "failed_count": 1,
    "read_count": 2,
}
NOTIFICATION_MARK_READ_EXAMPLE = {
    "success": True,
    "marked_count": 1,
    "message": "1 notification(s) marked as read",
}

ROOT_EXAMPLE = {"message": "Welcome to OrderRun API", "version": "0.1.0", "docs": "/docs"}
HEALTH_EXAMPLE = {"success": True, "data": {"status": "UP"}, "message": "Success"}
