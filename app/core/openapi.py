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
EXAMPLE_ORDERER_NAME = "홍길동"
EXAMPLE_RUNNER_NAME = "Runner One"
EXAMPLE_ORDERER_LEVEL = 0
EXAMPLE_RUNNER_LEVEL = 3
EXAMPLE_CREATED_AT = "2026-06-01T12:00:00+09:00"
EXAMPLE_UPDATED_AT = "2026-06-01T12:10:00+09:00"
EXAMPLE_DEADLINE = "2026-06-02T12:00:00+09:00"

USER_DETAIL_EXAMPLE = {
    "success": True,
    "data": {
        "id": EXAMPLE_USER_ID,
        "name": EXAMPLE_ORDERER_NAME,
        "phone": "01012345678",
        "phoneVerifiedAt": EXAMPLE_CREATED_AT,
        "createdAt": EXAMPLE_CREATED_AT,
        "lastLoginAt": EXAMPLE_UPDATED_AT,
        "alarmEnabled": False,
        "level": EXAMPLE_ORDERER_LEVEL,
    },
    "message": None,
}
USER_ALARM_EXAMPLE = {"success": True, "data": None, "message": "알람 설정이 업데이트되었습니다."}
USER_NAME_EXAMPLE = {"success": True, "data": None, "message": "닉네임이 업데이트되었습니다."}
USER_FCM_TOKEN_EXAMPLE = {"success": True, "data": None, "message": "FCM 토큰이 업데이트되었습니다."}
USER_WITHDRAWAL_REASONS_EXAMPLE = {
    "success": True,
    "data": [
        {
            "id": 1,
            "questionText": "원하는 임무가 많지 않았어요.",
            "displayOrder": 1,
            "requiresDetail": False,
        }
    ],
    "message": "Success",
}
USER_WITHDRAWAL_EXAMPLE = {"success": True, "data": None, "message": "회원 탈퇴가 완료되었습니다."}

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

DISPUTE_SURVEY_QUESTIONS_EXAMPLE = {
    "success": True,
    "data": [
        {
            "id": 1,
            "targetType": "ORDER",
            "questionText": "러너의 수행 결과에 어떤 문제가 있었나요?",
            "displayOrder": 1,
        }
    ],
    "message": "Success",
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
    "ordererId": EXAMPLE_USER_ID,
    "ordererName": EXAMPLE_ORDERER_NAME,
    "ordererLevel": EXAMPLE_ORDERER_LEVEL,
    "matchedAt": None,
    "runnerConfirmedAt": None,
    "ordererConfirmedAt": None,
    "disputedAt": None,
    "resolvedAt": None,
    "openChatUrl": None,
    "offers": [],
}
PROPOSAL_WAITING_OFFER_EXAMPLE = {
    "id": 10,
    "proposalId": 1,
    "runnerId": EXAMPLE_RUNNER_ID,
    "runnerName": EXAMPLE_RUNNER_NAME,
    "runnerLevel": EXAMPLE_RUNNER_LEVEL,
    "status": "WAITING",
    "createdAt": EXAMPLE_CREATED_AT,
}
PROPOSAL_ACCEPTED_OFFER_EXAMPLE = {
    **PROPOSAL_WAITING_OFFER_EXAMPLE,
    "status": "ACCEPTED",
}
PROPOSAL_ALL_COMPLETED_OFFER_EXAMPLE = {
    **PROPOSAL_WAITING_OFFER_EXAMPLE,
    "status": "ALL_COMPLETED",
}
PROPOSAL_DISPUTED_OFFER_EXAMPLE = {
    **PROPOSAL_WAITING_OFFER_EXAMPLE,
    "status": "DISPUTED",
}
PROPOSAL_RESOLVED_OFFER_EXAMPLE = {
    **PROPOSAL_WAITING_OFFER_EXAMPLE,
    "status": "RESOLVED",
}
PROPOSAL_CANCELLED_OFFER_EXAMPLE = {
    **PROPOSAL_WAITING_OFFER_EXAMPLE,
    "status": "CANCELLED",
}
PROPOSAL_HOLDING_DETAIL_EXAMPLE = {
    **PROPOSAL_EXAMPLE,
    **PROPOSAL_STATE_TIMESTAMPS,
    "status": "HOLDING",
}
PROPOSAL_POSTED_DETAIL_EXAMPLE = {**PROPOSAL_EXAMPLE, **PROPOSAL_STATE_TIMESTAMPS}
PROPOSAL_DETAIL_EXAMPLE = PROPOSAL_POSTED_DETAIL_EXAMPLE
PROPOSAL_OFFERED_DETAIL_EXAMPLE = {
    **PROPOSAL_EXAMPLE,
    **PROPOSAL_STATE_TIMESTAMPS,
    "status": "OFFERED",
    "offers": [PROPOSAL_WAITING_OFFER_EXAMPLE],
}
PROPOSAL_MATCHED_DETAIL_EXAMPLE = {
    **PROPOSAL_EXAMPLE,
    **PROPOSAL_STATE_TIMESTAMPS,
    "status": "MATCHED",
    "matchedAt": EXAMPLE_UPDATED_AT,
    "openChatUrl": "https://open.kakao.com/o/example",
    "offers": [PROPOSAL_ACCEPTED_OFFER_EXAMPLE],
}
PROPOSAL_ORDER_COMPLETED_DETAIL_EXAMPLE = {
    **PROPOSAL_MATCHED_DETAIL_EXAMPLE,
    "status": "ORDER_COMPLETED",
    "ordererConfirmedAt": EXAMPLE_UPDATED_AT,
}
PROPOSAL_ALL_COMPLETED_DETAIL_EXAMPLE = {
    **PROPOSAL_MATCHED_DETAIL_EXAMPLE,
    "status": "ALL_COMPLETED",
    "runnerConfirmedAt": EXAMPLE_UPDATED_AT,
    "ordererConfirmedAt": EXAMPLE_UPDATED_AT,
    "offers": [PROPOSAL_ALL_COMPLETED_OFFER_EXAMPLE],
}
PROPOSAL_DISPUTED_DETAIL_EXAMPLE = {
    **PROPOSAL_MATCHED_DETAIL_EXAMPLE,
    "status": "DISPUTED",
    "disputedAt": EXAMPLE_UPDATED_AT,
    "offers": [PROPOSAL_DISPUTED_OFFER_EXAMPLE],
}
PROPOSAL_RESOLVED_DETAIL_EXAMPLE = {
    **PROPOSAL_DISPUTED_DETAIL_EXAMPLE,
    "status": "RESOLVED",
    "resolvedAt": EXAMPLE_UPDATED_AT,
    "offers": [PROPOSAL_RESOLVED_OFFER_EXAMPLE],
}
PROPOSAL_CANCELLED_DETAIL_EXAMPLE = {
    **PROPOSAL_EXAMPLE,
    **PROPOSAL_STATE_TIMESTAMPS,
    "status": "CANCELLED",
    "offers": [PROPOSAL_CANCELLED_OFFER_EXAMPLE],
}
PROPOSAL_DETAIL_EXAMPLES = {
    "holding": {"success": True, "data": PROPOSAL_HOLDING_DETAIL_EXAMPLE, "message": None},
    "posted": {"success": True, "data": PROPOSAL_POSTED_DETAIL_EXAMPLE, "message": None},
    "offered": {"success": True, "data": PROPOSAL_OFFERED_DETAIL_EXAMPLE, "message": None},
    "matched": {"success": True, "data": PROPOSAL_MATCHED_DETAIL_EXAMPLE, "message": None},
    "order_completed": {"success": True, "data": PROPOSAL_ORDER_COMPLETED_DETAIL_EXAMPLE, "message": None},
    "all_completed": {"success": True, "data": PROPOSAL_ALL_COMPLETED_DETAIL_EXAMPLE, "message": None},
    "disputed": {"success": True, "data": PROPOSAL_DISPUTED_DETAIL_EXAMPLE, "message": None},
    "resolved": {"success": True, "data": PROPOSAL_RESOLVED_DETAIL_EXAMPLE, "message": None},
    "cancelled": {"success": True, "data": PROPOSAL_CANCELLED_DETAIL_EXAMPLE, "message": None},
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
    "ordererName": EXAMPLE_ORDERER_NAME,
    "ordererLevel": EXAMPLE_ORDERER_LEVEL,
    "offerCount": 1,
    "offers": [
        {
            "id": 10,
            "proposalId": 1,
            "runnerId": EXAMPLE_RUNNER_ID,
            "runnerName": EXAMPLE_RUNNER_NAME,
            "runnerLevel": EXAMPLE_RUNNER_LEVEL,
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
    "data": PROPOSAL_ORDER_COMPLETED_DETAIL_EXAMPLE,
    "message": "완료 확인되었습니다.",
}
PROPOSAL_ALL_COMPLETED_RECEIVED_EXAMPLE = {
    "success": True,
    "data": PROPOSAL_ALL_COMPLETED_DETAIL_EXAMPLE,
    "message": "완료 확인되었습니다.",
}
PROPOSAL_DISPUTE_EXAMPLE = {
    "success": True,
    "data": PROPOSAL_DISPUTED_DETAIL_EXAMPLE,
    "message": "분쟁이 접수되었습니다.",
}
DISPUTE_EVIDENCE_EXAMPLE = {
    "success": True,
    "data": {
        "id": 1,
        "proposalId": 1,
        "offerId": 10,
        "actorId": EXAMPLE_RUNNER_ID,
        "reason": "배송 중 파손",
        "surveyQuestionId": 3,
        "createdAt": EXAMPLE_CREATED_AT,
    },
    "message": "Success",
}

OFFER_EXAMPLE = {
    "id": 10,
    "proposalId": 1,
    "ordererId": EXAMPLE_USER_ID,
    "ordererName": EXAMPLE_ORDERER_NAME,
    "ordererLevel": EXAMPLE_ORDERER_LEVEL,
    "runnerId": EXAMPLE_RUNNER_ID,
    "runnerName": EXAMPLE_RUNNER_NAME,
    "runnerLevel": EXAMPLE_RUNNER_LEVEL,
    "status": "WAITING",
    "acceptedAt": None,
    "runnerConfirmedAt": None,
    "ordererConfirmedAt": None,
    "disputedAt": None,
    "resolvedAt": None,
    "createdAt": EXAMPLE_CREATED_AT,
}
OFFER_WAITING_EXAMPLE = OFFER_EXAMPLE
OFFER_ACCEPTED_EXAMPLE = {**OFFER_EXAMPLE, "status": "ACCEPTED", "acceptedAt": EXAMPLE_UPDATED_AT}
OFFER_RUNNER_COMPLETED_EXAMPLE = {
    **OFFER_EXAMPLE,
    "status": "RUNNER_COMPLETED",
    "acceptedAt": EXAMPLE_CREATED_AT,
    "runnerConfirmedAt": EXAMPLE_UPDATED_AT,
}
OFFER_ALL_COMPLETED_EXAMPLE = {
    **OFFER_RUNNER_COMPLETED_EXAMPLE,
    "status": "ALL_COMPLETED",
    "ordererConfirmedAt": EXAMPLE_UPDATED_AT,
}
OFFER_DISPUTED_STATUS_EXAMPLE = {
    **OFFER_EXAMPLE,
    "status": "DISPUTED",
    "acceptedAt": EXAMPLE_CREATED_AT,
    "disputedAt": EXAMPLE_UPDATED_AT,
}
OFFER_RESOLVED_STATUS_EXAMPLE = {
    **OFFER_DISPUTED_STATUS_EXAMPLE,
    "status": "RESOLVED",
    "resolvedAt": EXAMPLE_UPDATED_AT,
}
OFFER_REJECTED_EXAMPLE = {**OFFER_EXAMPLE, "status": "REJECTED"}
OFFER_CANCELLED_EXAMPLE = {**OFFER_EXAMPLE, "status": "CANCELLED"}
OFFER_STATUS_DATA_EXAMPLES = {
    "waiting": OFFER_WAITING_EXAMPLE,
    "accepted": OFFER_ACCEPTED_EXAMPLE,
    "runner_completed": OFFER_RUNNER_COMPLETED_EXAMPLE,
    "all_completed": OFFER_ALL_COMPLETED_EXAMPLE,
    "disputed": OFFER_DISPUTED_STATUS_EXAMPLE,
    "resolved": OFFER_RESOLVED_STATUS_EXAMPLE,
    "rejected": OFFER_REJECTED_EXAMPLE,
    "cancelled": OFFER_CANCELLED_EXAMPLE,
}
OFFER_OPEN_CHAT_EXAMPLE = "https://open.kakao.com/o/example"
OFFER_OPEN_CHAT_EXAMPLE_STATUSES = {
    "accepted",
    "runner_completed",
    "all_completed",
    "disputed",
    "resolved",
}
OFFER_DETAIL_EXAMPLES = {
    name: {
        "success": True,
        "data": {
            **data,
            "openChatUrl": OFFER_OPEN_CHAT_EXAMPLE if name in OFFER_OPEN_CHAT_EXAMPLE_STATUSES else None,
        },
        "message": "Success",
    }
    for name, data in OFFER_STATUS_DATA_EXAMPLES.items()
}
OFFER_LIST_EXAMPLES = {
    name: {"success": True, "data": [data], "message": "Success"}
    for name, data in OFFER_STATUS_DATA_EXAMPLES.items()
}
OFFER_PAGE_EXAMPLES = {
    name: {
        "success": True,
        "data": {
            "content": [data],
            "totalElements": 1,
            "totalPages": 1,
            "pageNumber": 0,
            "pageSize": 20,
            "first": True,
            "last": True,
        },
        "message": "Success",
    }
    for name, data in OFFER_STATUS_DATA_EXAMPLES.items()
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
OFFER_ACCEPTED_DETAIL_EXAMPLE = OFFER_DETAIL_EXAMPLES["accepted"]
OFFER_COMPLETE_DELIVERY_EXAMPLES = {
    "runner_completed": {
        "success": True,
        "data": OFFER_RUNNER_COMPLETED_EXAMPLE,
        "message": "완료 처리되었습니다.",
    },
    "all_completed": {
        "success": True,
        "data": OFFER_ALL_COMPLETED_EXAMPLE,
        "message": "완료 처리되었습니다.",
    },
}
OFFER_DISPUTE_EXAMPLE = {
    "success": True,
    "data": OFFER_DISPUTED_STATUS_EXAMPLE,
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
        "ordererName": EXAMPLE_ORDERER_NAME,
        "ordererLevel": EXAMPLE_ORDERER_LEVEL,
        "runnerId": EXAMPLE_RUNNER_ID,
        "runnerName": EXAMPLE_RUNNER_NAME,
        "runnerLevel": EXAMPLE_RUNNER_LEVEL,
        "acceptedAt": EXAMPLE_CREATED_AT,
    },
    "message": "제안이 수락되었습니다.",
}

OFFER_RESOLVED_EXAMPLE = {
    "success": True,
    "data": OFFER_RESOLVED_STATUS_EXAMPLE,
    "message": "제안 분쟁이 해결되었습니다.",
}

SETTLEMENT_ACCOUNT_EXAMPLE = {
    "bankName": "국민은행",
    "accountHolder": "홍길동",
    "maskedAccountNumber": "********9012",
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
    "success": True,
    "data": {
        "total": 1,
        "notifications": [NOTIFICATION_EXAMPLE],
        "page": 1,
        "page_size": 20,
    },
    "message": "Success",
}
NOTIFICATION_STATS_EXAMPLE = {
    "success": True,
    "data": {
        "total_notifications": 3,
        "unread_count": 1,
        "failed_count": 1,
        "read_count": 2,
    },
    "message": "Success",
}
NOTIFICATION_MARK_READ_EXAMPLE = {
    "success": True,
    "data": {"marked_count": 1},
    "message": "1 notification(s) marked as read",
}
NOTIFICATION_RESPONSE_EXAMPLE = {"success": True, "data": NOTIFICATION_EXAMPLE, "message": "Success"}

ROOT_EXAMPLE = {"message": "Welcome to OrderRun API", "version": "0.1.0", "docs": "/docs"}
HEALTH_EXAMPLE = {"success": True, "data": {"status": "UP"}, "message": "Success"}
