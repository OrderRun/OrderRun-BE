# OrderRun API 명세서

이 문서는 OrderRun 외부 API의 요청/응답 계약을 한 곳에서 확인하기 위한 진입점이자 통합 명세서다.

- Base URL: `/v1`
- Content-Type: `application/json`
- 인증: `Authorization: Bearer {access_token}`
- 구현 갭 점검: [`implementation-gaps.md`](./implementation-gaps.md)
- 도메인 정책 정본: [`../domain.md`](../domain.md)

## 공통 규칙

### 성공 응답

모든 성공 응답은 `ApiResponse<T>`를 기본 래퍼로 사용한다. 단, `DELETE /v1/offer/{offerId}`는 `204 No Content`로 본문을 반환하지 않는다.

```json
{
  "success": true,
  "data": {},
  "message": "Success"
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| success | boolean | 성공 여부. 성공 응답은 `true` |
| data | object, array, null | API별 응답 데이터 |
| message | string | 처리 결과 메시지 |

### 페이징 응답

페이징 목록은 `data`에 `PageResponse<T>`를 담아 반환한다.

| 필드 | 타입 | 설명 |
|------|------|------|
| content | array | 현재 페이지 데이터 목록 |
| totalElements | number | 전체 요소 수 |
| totalPages | number | 전체 페이지 수 |
| pageNumber | number | 현재 페이지 번호. 0부터 시작 |
| pageSize | number | 페이지 크기 |
| first | boolean | 첫 페이지 여부 |
| last | boolean | 마지막 페이지 여부 |

### 에러 응답

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지",
    "details": "상세 정보"
  },
  "timestamp": "2026-05-30T12:00:00Z"
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| success | boolean | 실패 응답은 `false` |
| error.code | string | `ErrorCode`의 외부 코드 |
| error.message | string | 사용자에게 전달 가능한 에러 메시지 |
| error.details | string, object, null | 상세 정보. 없을 수 있음 |
| timestamp | string | 에러 발생 시각 |

### Swagger 문서화 규칙

Swagger UI는 `/docs`, OpenAPI JSON은 `/openapi.json`에서 확인한다.

- API 제목과 전체 설명은 `app/main.py`의 `FastAPI(...)` 설정을 사용한다.
- API별 요약과 설명은 `app/api/v1/*` 라우터 데코레이터의 `summary`, `description`을 사용한다.
- 요청/응답 필드 설명은 `app/schemas/*`의 Pydantic `Field(description=...)`을 사용한다.
- 각 API 요청/응답은 endpoint별 독립 DTO를 기준으로 문서화하며, API DTO가 다른 API DTO를 상속해 계약을 공유하지 않는다.
- 성공 응답 예시는 실제 통합 테스트의 응답 구조를 기준으로 `app/core/openapi.py`의 `success_response()`와 고정 예시 상수를 사용한다.
- 실패 응답 예시는 `app/core/openapi.py`의 `error_responses()`로 생성하며, 에러 코드와 메시지는 `app/core/errors.py`의 `AppError` 카탈로그를 기준으로 한다.
- Swagger 실패 응답 예시는 실제 예외 핸들러 응답과 같은 `success/error/timestamp` 형태를 유지한다.
- 요청 검증 실패는 실제 예외 핸들러와 동일하게 400 실패 응답으로 문서화하며, FastAPI 기본 422 문서는 노출하지 않는다.

### 인증 예외

아래 API는 인증 없이 호출할 수 있다.

- `GET /v1/health`
- `POST /v1/auth/signup/send`
- `POST /v1/auth/signup/confirm`
- `POST /v1/auth/login/send`
- `POST /v1/auth/login/confirm`
- `POST /v1/auth/refresh`

그 외 API는 Bearer access token이 필요하다.

### 공통 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| page | integer | X | 0 | 페이지 번호 |
| size | integer | X | 컨트롤러 기본값 | 페이지 크기 |
| sort | string | X | API별 기본값 | Spring Pageable 정렬. 예: `createdAt,desc` |

## 공통 스키마

### AuthVerificationSendResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| phone | string | 정규화된 전화번호 |
| expiresAt | string | 인증 코드 만료 시각. ISO-8601 Instant |

### AuthTokenResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| accessToken | string | API 인증에 사용할 access token |
| refreshToken | string | access token 갱신에 사용할 refresh token |
| tokenType | string | 토큰 타입. 현재 `Bearer` |
| expiresIn | number | access token 만료까지 남은 시간. 밀리초 |
| userId | string | 로그인 사용자 ID |

### TokenRefreshResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| accessToken | string | 새 access token |
| expiresIn | number | access token 만료까지 남은 시간. 밀리초 |

### UserDetailResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| id | string | 사용자 ID |
| name | string | 사용자 이름 |
| phone | string | 정규화된 전화번호 |
| phoneVerifiedAt | string, null | 전화번호 인증 완료 시각 |
| createdAt | string | 가입 시각 |
| lastLoginAt | string, null | 마지막 로그인 시각 |
| alarmEnabled | boolean | 알람 수신 동의 여부 |

### ProposalResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| id | number | Proposal ID |
| title | string | 공고 제목 |
| content | string | 요청 상세 내용 |
| deadline | string | 수행 마감 시각. ISO-8601 Instant |
| errandFee | number | 러너에게 지급할 심부름비 |
| status | string | Proposal 상태. `ProposalStatus` 참조 |

### ProposalOwnResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| id | number | Proposal ID |
| ordererId | string | 작성자 사용자 ID |
| title | string | 공고 제목 |
| content | string | 요청 상세 내용 |
| deadline | string | 수행 마감 시각 |
| errandFee | number | 심부름비 |
| status | string | Proposal 상태 |
| offerCount | number | 연결된 Offer 개수 |
| offers | array | `ProposalOwnOfferResponse[]` |
| createdAt | string | 생성 시각 |
| updatedAt | string | 수정 시각 |

### ProposalOwnOfferResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| id | number | Offer ID |
| proposalId | number | 대상 Proposal ID |
| runnerId | string | Offer 제출 러너 ID |
| status | string | Offer 상태 |
| createdAt | string | Offer 생성 시각 |

### ProposalDetailResponse

`ProposalResponse`와 동일한 필드에 다음 필드를 추가로 반환한다.

| 필드 | 타입 | 설명 |
|------|------|------|
| matchedAt | string, null | Offer 수락으로 매칭된 시각 |
| deliveryReportedAt | string, null | 러너 완료가 Proposal에 반영된 시각 |
| receivedConfirmedAt | string, null | 오더러 완료 확인 시각 |
| settledAt | string, null | 정산 완료 시각 |
| disputedAt | string, null | 분쟁 접수 시각 |
| refundedAt | string, null | 환불 완료 시각 |

### OfferResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| id | number | Offer ID |
| proposalId | number | 대상 Proposal ID |
| runnerId | string | Offer 제출 러너 ID |
| runnerName | string, null | Offer 제출 러너 이름 |
| status | string | Offer 상태. `OfferStatus` 참조 |
| acceptedAt | string, null | 오더가 Offer를 수락한 시각 |
| deliveryCompletedAt | string, null | 러너 완료 시각 |
| receiptConfirmedAt | string, null | 오더러 완료 확인이 Offer에 반영된 시각 |
| settledAt | string, null | 정산 완료 시각 |
| disputedAt | string, null | 분쟁 접수 시각 |
| refundedAt | string, null | 환불 완료 시각 |
| createdAt | string | Offer 생성 시각 |

### OfferAcceptResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| proposalId | number | 연결된 Proposal ID |
| offerId | number | 수락된 Offer ID |
| proposalStatus | string | 수락 후 Proposal 상태 |
| acceptedOfferStatus | string | 수락된 Offer 상태 |
| rejectedOfferCount | number | 자동 거절된 다른 Offer 개수 |
| ordererId | string | 오더 사용자 ID 스냅샷 |
| runnerId | string | 러너 사용자 ID 스냅샷 |
| acceptedAt | string | Offer 수락 시각 |

### ProofResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| id | number | Proof ID |
| proposalId | number | 연결된 Proposal ID |
| offerId | number | 연결된 Offer ID |
| actorId | string | 증빙을 남긴 사용자 ID |
| proofType | string | `DELIVERY` 또는 `DISPUTE` |
| imageUrl | string, null | 배송 사진 URL |
| reason | string, null | 분쟁 사유 |
| createdAt | string | Proof 생성 시각 |

### SettlementAccountResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| bankCode | string | 은행 코드 |
| bankName | string | 은행명 |
| maskedAccountNumber | string | 마스킹된 계좌번호 |
| accountHolder | string | 예금주명 |
| updatedAt | string | 수정 시각 |

### TermsAgreementResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| userId | string | 사용자 ID |
| termsOfService | boolean | 이용약관 동의 여부 |
| privacyPolicy | boolean | 개인정보처리방침 동의 여부 |
| paymentRefundPolicy | boolean | 결제/환불지급정책 동의 여부 |
| agreedAt | string | 약관 동의 시각 |

## API 목록

### Health API

| 기능 | Method | Path | 인증 | 성공 상태 | 응답 data |
|------|--------|------|------|-----------|-----------|
| 헬스체크 | `GET` | `/v1/health` | 불필요 | `200 OK` | `{ "status": "UP" }` |

### Auth API

| 기능 | Method | Path | 인증 | 성공 상태 | 응답 data |
|------|--------|------|------|-----------|-----------|
| 회원가입 인증코드 발송 | `POST` | `/v1/auth/signup/send` | 불필요 | `200 OK` | `AuthVerificationSendResponse` |
| 회원가입 인증코드 확인 | `POST` | `/v1/auth/signup/confirm` | 불필요 | `200 OK` | `AuthTokenResponse` |
| 로그인 인증코드 발송 | `POST` | `/v1/auth/login/send` | 불필요 | `200 OK` | `AuthVerificationSendResponse` |
| 로그인 인증코드 확인 | `POST` | `/v1/auth/login/confirm` | 불필요 | `200 OK` | `AuthTokenResponse` |
| 토큰 갱신 | `POST` | `/v1/auth/refresh` | 불필요 | `200 OK` | `TokenRefreshResponse` |
| 로그아웃 | `POST` | `/v1/auth/logout` | 필요 | `200 OK` | `null` |

### User API

| 기능 | Method | Path | 인증 | 성공 상태 | 응답 data |
|------|--------|------|------|-----------|-----------|
| 알람 수신 동의 업데이트 | `POST` | `/v1/user/alarm` | 필요 | `200 OK` | `null` |
| FCM 토큰 갱신 | `PATCH` | `/v1/user/fcm-token` | 필요 | `200 OK` | `null` |
| 사용자 프로필 조회 | `GET` | `/v1/user/detail` | 필요 | `200 OK` | `UserDetailResponse` |

### Terms API

| 기능 | Method | Path | 인증 | 성공 상태 | 응답 data |
|------|--------|------|------|-----------|-----------|
| 약관 동의 | `POST` | `/v1/terms` | 필요 | `201 Created` | `TermsAgreementResponse` |

### Proposal API

| 기능 | Method | Path | 인증 | 성공 상태 | 응답 data |
|------|--------|------|------|-----------|-----------|
| 요청 게시글 목록 조회 | `GET` | `/v1/proposal` | 필요 | `200 OK` | `PageResponse<ProposalResponse>` |
| 요청 게시글 상세 조회 | `GET` | `/v1/proposal/{id}` | 필요 | `200 OK` | `ProposalDetailResponse` |
| 내 요청 게시글 목록 조회 | `GET` | `/v1/proposal/own` | 필요 | `200 OK` | `PageResponse<ProposalOwnResponse>` |
| 요청 게시글 등록 | `POST` | `/v1/proposal` | 필요 | `201 Created` | `ProposalResponse` |
| 요청 게시글 수정 | `PUT` | `/v1/proposal/{id}` | 필요. 작성자만 가능 | `200 OK` | `ProposalResponse` |
| 요청 게시글 취소 | `POST` | `/v1/proposal/{id}/cancel` | 필요. 작성자만 가능 | `200 OK` | `ProposalResponse` |
| 오더 수령 확인 | `POST` | `/v1/proposal/{id}/confirm-received` | 필요. 작성자만 가능 | `200 OK` | `ProposalDetailResponse` |
| 오더 분쟁 접수 | `POST` | `/v1/proposal/{id}/dispute` | 필요. 작성자만 가능 | `200 OK` | `ProposalDetailResponse` |

### Offer API

| 기능 | Method | Path | 인증 | 성공 상태 | 응답 data |
|------|--------|------|------|-----------|-----------|
| 오퍼 제출 | `POST` | `/v1/offer` | 필요 | `201 Created` | `OfferResponse` |
| 오퍼 수락 | `POST` | `/v1/offer/{offerId}/accept` | 필요. 연결된 Proposal 작성자만 가능 | `201 Created` | `OfferAcceptResponse` |
| 오퍼 상세 조회 | `GET` | `/v1/offer/{offerId}` | 필요 | `200 OK` | `OfferResponse` |
| Proposal별 오퍼 목록 조회 | `GET` | `/v1/offer?proposalId={id}` | 필요 | `200 OK` | `OfferResponse[]` |
| 내 오퍼 목록 조회 | `GET` | `/v1/offer/own` | 필요 | `200 OK` | `PageResponse<OfferResponse>` |
| 러너 전달 완료 | `POST` | `/v1/offer/{offerId}/complete-delivery` | 필요. Offer 제출 러너만 가능 | `200 OK` | `OfferResponse` |
| 러너 분쟁 접수 | `POST` | `/v1/offer/{offerId}/dispute` | 필요. Offer 제출 러너만 가능 | `200 OK` | `OfferResponse` |
| 오퍼 취소 | `DELETE` | `/v1/offer/{offerId}` | 필요. Offer 제출 러너만 가능 | `204 No Content` | 없음 |

### Admin Execution API

Mission API는 제거되었고 관리자 정산/환불은 수락된 Offer ID 기준으로 처리한다.

| 기능 | Method | Path | 인증 | 성공 상태 | 응답 data |
|------|--------|------|------|-----------|-----------|
| Offer 정산 완료 | `POST` | `/api/v1/admin/offer/{offerId}/confirm-settlement` | 관리자 필요 | `200 OK` | `OfferResponse` |
| Offer 환불 완료 | `POST` | `/api/v1/admin/offer/{offerId}/refund` | 관리자 필요 | `200 OK` | `OfferResponse` |

### Settlement API

| 기능 | Method | Path | 인증 | 성공 상태 | 응답 data |
|------|--------|------|------|-----------|-----------|
| 정산 계좌 조회 | `GET` | `/v1/settlement/account` | 필요 | `200 OK` | `SettlementAccountResponse` 또는 `null` |
| 정산 계좌 저장 | `PUT` | `/v1/settlement/account` | 필요 | `200 OK` | `SettlementAccountResponse` |

## 요청 명세

### Auth

#### `POST /v1/auth/signup/send`

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| name | string | O | 공백 불가, 최대 100자 |
| phone | string | O | 공백 불가, 최대 20자, `^[0-9+\-\s]{8,20}$` |
| carrier | string | O | 공백 불가, 최대 50자 |

#### `POST /v1/auth/signup/confirm`

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| phone | string | O | 공백 불가, 최대 20자, `^[0-9+\-\s]{8,20}$` |
| code | string | O | 6자리 숫자 |

#### `POST /v1/auth/login/send`

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| phone | string | O | 공백 불가, 최대 20자, `^[0-9+\-\s]{8,20}$` |

#### `POST /v1/auth/login/confirm`

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| phone | string | O | 공백 불가, 최대 20자, `^[0-9+\-\s]{8,20}$` |
| code | string | O | 6자리 숫자 |
| fcmToken | string | X | 최대 4096자 |

#### `POST /v1/auth/refresh`, `POST /v1/auth/logout`

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| refreshToken | string | O | 공백 불가 |

### Terms

#### `POST /v1/terms`

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| termsOfService | boolean | O | 반드시 `true` |
| privacyPolicy | boolean | O | 반드시 `true` |
| paymentRefundPolicy | boolean | O | 반드시 `true` |

### Proposal

#### `GET /v1/proposal`

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| status | array[string] | X | 없음 | Proposal 상태 필터. 반복 입력 가능: `status=A&status=B`. 없으면 전체 상태 |
| page | integer | X | 0 | 페이지 번호 |
| size | integer | X | 20 | 페이지 크기 |
| sort | string | X | `createdAt,desc` | 정렬 |

#### `GET /v1/proposal/own`

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| status | array[string] | X | 없음 | Proposal 상태 필터. 반복 입력 가능: `status=A&status=B`. 없으면 전체 상태 |
| page | integer | X | 0 | 페이지 번호 |
| size | integer | X | 20 | 페이지 크기 |
| sort | string | X | `createdAt,desc` | 정렬 |

#### `POST /v1/proposal`, `PUT /v1/proposal/{id}`

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| title | string | O | 공백 불가, 최대 50자 |
| content | string | O | 공백 불가, 최대 500자 |
| deadline | string | O | 오프셋 포함 ISO-8601 문자열, 현재보다 미래 |
| errandFee | integer | O | 1000원 이상 |

### Offer

#### `POST /v1/offer`

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| proposalId | number | O | 1 이상 |

#### `POST /v1/offer/{offerId}/accept`

요청 본문 없음.

#### `POST /v1/offer/{offerId}/complete-delivery`

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| proofImageUrl | string | X | 완료 인증 이미지 URL |

#### `POST /v1/offer/{offerId}/dispute`

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| disputeReason | string | O | 분쟁 사유 |

#### `GET /v1/offer`

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| proposalId | number | O | Proposal ID |
| status | array[string] | X | Offer 상태 필터. 반복 입력 가능: `status=A&status=B`. 없으면 전체 상태 |

#### `GET /v1/offer/own`

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| status | array[string] | X | 없음 | Offer 상태 필터. 반복 입력 가능: `status=A&status=B`. 없으면 전체 상태 |
| page | integer | X | 0 | 페이지 번호 |
| size | integer | X | 20 | 페이지 크기 |

#### `POST /v1/proposal/{proposalId}/confirm-received`

요청 본문 없음.

#### `POST /v1/proposal/{proposalId}/dispute`

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| disputeReason | string | O | 분쟁 사유 |

### Settlement

#### `PUT /v1/settlement/account`

| 필드 | 타입 | 필수 | 제약 |
|------|------|------|------|
| bankCode | string | O | 숫자 2~10자리 |
| bankName | string | O | 공백 불가, 최대 50자 |
| accountNumber | string | O | 숫자 6~30자리 |
| accountHolder | string | O | 공백 불가, 최대 100자 |

## 상태 Enum

### ProposalStatus

| 값 | 설명 |
|----|------|
| HOLDING | 입금 확인 대기 |
| POSTED | 모집 중 |
| OFFERED | 제안 도착 |
| MATCHED | 매칭 완료 |
| COMPLETED | 오더러 완료 확인 |
| ALL_COMPLETED | 러너와 오더러 모두 완료 |
| SETTLED | 정산 완료 |
| DISPUTED | 분쟁 접수 |
| REFUNDED | 환불 완료 |
| CANCELLED | 취소됨 |

### OfferStatus

| 값 | 설명 |
|----|------|
| WAITING | 수락 대기 |
| ACCEPTED | 수락됨 |
| COMPLETED | 러너 완료 |
| ALL_COMPLETED | 러너와 오더러 모두 완료 |
| SETTLED | 정산 완료 |
| DISPUTED | 분쟁 접수 |
| REFUNDED | 환불 완료 |
| REJECTED | 거절됨 |
| CANCELLED | 취소됨 |

### ProofType

| 값 | 설명 |
|----|------|
| DELIVERY | 완료 증빙 |
| DISPUTE | 분쟁 사유 등 분쟁 증빙 |

Mission 도메인과 Mission 상태 enum은 제거되었다.

## 에러 코드

| HTTP | ErrorCode | 설명 |
|------|-----------|------|
| 400 | `VALIDATION_ERROR` | 요청 값 검증 실패 |
| 400 | `INVALID_REQUEST_PARAMETER` | 요청 파라미터 오류 |
| 400 | `INVALID_DATE_TIME_FORMAT` | 시간 입력 형식 오류 |
| 400 | `PROPOSAL_DEADLINE_INVALID` | Proposal 마감 시각이 미래가 아님 |
| 400 | `PROPOSAL_MEETING_AT_INVALID` | 만남일이 미래가 아님 |
| 400 | `PROPOSAL_ERRAND_FEE_INVALID` | 심부름비가 1000원 미만 |
| 400 | `PROPOSAL_ITEM_PRICE_INVALID` | 제품 가격이 0원 미만 |
| 400 | `PROPOSAL_DEPOSIT_INVALID` | 보증금이 0원 미만 |
| 400 | `PHONE_VERIFICATION_EXPIRED` | 전화번호 인증 코드 만료 |
| 400 | `PHONE_VERIFICATION_CODE_MISMATCH` | 전화번호 인증 코드 불일치 |
| 401 | `INVALID_CREDENTIALS` | 인증 정보 오류 |
| 401 | `INVALID_TOKEN` | 유효하지 않은 토큰 |
| 401 | `EXPIRED_TOKEN` | 만료된 토큰 |
| 403 | `FORBIDDEN` | 권한 없음 |
| 404 | `USER_NOT_FOUND` | 사용자를 찾을 수 없음 |
| 404 | `PHONE_VERIFICATION_NOT_FOUND` | 전화번호 인증 요청 없음 |
| 404 | `PROPOSAL_NOT_FOUND` | Proposal을 찾을 수 없음 |
| 404 | `OFFER_NOT_FOUND` | Offer를 찾을 수 없음 |
| 409 | `PHONE_ALREADY_EXISTS` | 이미 사용 중인 전화번호 |
| 409 | `PHONE_VERIFICATION_ALREADY_SENT` | 만료되지 않은 인증 코드가 이미 있음 |
| 409 | `DUPLICATE_OFFER` | 동일 Proposal에 중복 Offer 제출 |
| 409 | `PROPOSAL_NOT_OPEN` | Offer를 받을 수 없는 Proposal 상태 |
| 409 | `PROPOSAL_NOT_MATCHABLE` | 매칭할 수 없는 Proposal 상태 |
| 409 | `PROPOSAL_NOT_EDITABLE` | 수정할 수 없는 Proposal 상태 |
| 409 | `PROPOSAL_NOT_CANCELLABLE` | 취소할 수 없는 Proposal 상태 |
| 409 | `PROPOSAL_NOT_UPDATABLE` | 변경할 수 없는 Proposal 상태 |
| 409 | `OFFER_NOT_ACCEPTABLE` | 수락할 수 없는 Offer 상태 |
| 409 | `OFFER_NOT_CANCELLABLE` | 취소할 수 없는 Offer 상태 |
| 409 | `OFFER_NOT_UPDATABLE` | 변경할 수 없는 Offer 상태 |
| 500 | `INTERNAL_SERVER_ERROR` | 알 수 없는 서버 오류 |

## 문서 정본 규칙

- 이 파일은 전체 API 요청/응답 스펙의 통합 명세로 유지한다.
- 상세 동작, 예시, 도메인별 추가 설명은 `docs/api-spec/` 하위 문서를 참고한다.
- 상태 전이와 정책 해석은 [`../domain.md`](../domain.md) 또는 관련 도메인 문서를 우선한다.
