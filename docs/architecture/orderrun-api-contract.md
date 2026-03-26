# OrderRun API 계약

## 1. 설계 원칙

- REST 스타일을 유지하되 상태 전이 엔드포인트는 명시적 액션 URI를 허용한다.
- 모든 API는 `JSON`을 사용한다.
- 버전은 `/api/v1` prefix로 관리한다.
- OpenAPI 문서와 Pydantic 스키마를 단일 진실 원천으로 사용한다.

## 2. 공통 규약

### 2.1 인증

- 기본 방식: `Authorization: Bearer <JWT>`
- 초기 학습 단계에서는 자체 로그인 또는 테스트 토큰 발급 엔드포인트를 둘 수 있다.
- 기존 Spring 분석에서 추정되는 임시 사용자 식별 헤더는 제거 대상이다.

### 2.2 응답 형식

성공 응답:

```json
{
  "success": true,
  "data": {},
  "meta": {
    "request_id": "req_123",
    "timestamp": "2026-03-19T00:00:00Z"
  }
}
```

실패 응답:

```json
{
  "success": false,
  "error": {
    "code": "PROPOSAL_NOT_FOUND",
    "message": "Proposal not found",
    "details": {}
  },
  "meta": {
    "request_id": "req_123",
    "timestamp": "2026-03-19T00:00:00Z"
  }
}
```

### 2.3 페이지네이션

- Query: `page`, `size`, `sort`
- 기본값: `page=1`, `size=20`
- 최대값: `size=100`

### 2.4 에러 코드 예시

| 코드 | HTTP | 설명 |
| --- | --- | --- |
| AUTH_REQUIRED | 401 | 인증 필요 |
| FORBIDDEN | 403 | 권한 없음 |
| USER_NOT_FOUND | 404 | 사용자 없음 |
| PROPOSAL_NOT_FOUND | 404 | 요청서 없음 |
| OFFER_NOT_FOUND | 404 | 제안 없음 |
| MISSION_NOT_FOUND | 404 | 미션 없음 |
| INVALID_STATE_TRANSITION | 409 | 상태 전이 불가 |
| DUPLICATE_OFFER | 409 | 중복 제안 |
| PAYMENT_PROVIDER_ERROR | 502 | 외부 결제 오류 |
| VALIDATION_ERROR | 422 | 입력값 검증 실패 |

## 3. API 카탈로그

상태 표기:

- `As-Is`: 기존 Spring 구현 또는 분석상 존재
- `To-Be`: FastAPI에서 목표로 구현
- `Gap`: 현행과 목표 사이에서 보완 필요

| Method | Path | 목적 | 상태 |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/token` | 테스트용 토큰 발급 | To-Be |
| GET | `/api/v1/users/me` | 내 정보 조회 | As-Is / To-Be |
| PATCH | `/api/v1/users/me` | 내 정보 수정 | As-Is / To-Be |
| GET | `/api/v1/users/{user_id}` | 사용자 프로필 조회 | To-Be |
| POST | `/api/v1/proposals` | 요청서 생성 | As-Is / To-Be |
| GET | `/api/v1/proposals` | 요청서 목록 조회 | As-Is / To-Be |
| GET | `/api/v1/proposals/{proposal_id}` | 요청서 상세 조회 | As-Is / To-Be |
| PATCH | `/api/v1/proposals/{proposal_id}` | 요청서 수정 | To-Be |
| POST | `/api/v1/proposals/{proposal_id}/publish` | 요청서 공개 | To-Be |
| POST | `/api/v1/proposals/{proposal_id}/cancel` | 요청서 취소 | To-Be |
| POST | `/api/v1/proposals/{proposal_id}/offers` | 제안 생성 | As-Is / To-Be |
| GET | `/api/v1/proposals/{proposal_id}/offers` | 제안 목록 조회 | As-Is / To-Be |
| POST | `/api/v1/offers/{offer_id}/accept` | 제안 수락 | As-Is / To-Be |
| POST | `/api/v1/offers/{offer_id}/reject` | 제안 거절 | To-Be |
| POST | `/api/v1/offers/{offer_id}/withdraw` | 제안 철회 | To-Be |
| GET | `/api/v1/missions/{mission_id}` | 미션 상세 조회 | As-Is / To-Be |
| POST | `/api/v1/missions/{mission_id}/start` | 미션 시작 | As-Is / To-Be |
| POST | `/api/v1/missions/{mission_id}/complete` | 미션 완료 | As-Is / To-Be |
| POST | `/api/v1/missions/{mission_id}/cancel` | 미션 취소 | To-Be |
| POST | `/api/v1/missions/{mission_id}/dispute` | 분쟁 등록 | To-Be |
| GET | `/api/v1/payments/{payment_id}` | 결제 상세 조회 | To-Be |
| POST | `/api/v1/payments/{payment_id}/capture` | 결제 확정 | To-Be |
| POST | `/api/v1/payments/{payment_id}/refund` | 환불 처리 | To-Be |
| GET | `/api/v1/terms/latest` | 최신 약관 조회 | To-Be |
| POST | `/api/v1/terms/agreements` | 약관 동의 등록 | To-Be |

## 4. 요청/응답 스키마

### 4.1 User

`UserProfileResponse`

```json
{
  "id": 1,
  "email": "user@example.com",
  "nickname": "runner-one",
  "role": "customer",
  "status": "active",
  "created_at": "2026-03-19T00:00:00Z"
}
```

`UserProfileUpdateRequest`

```json
{
  "nickname": "new-nickname",
  "phone_number": "01012345678"
}
```

### 4.2 Proposal

`ProposalCreateRequest`

```json
{
  "title": "대형마트 장보기 대행",
  "description": "우유, 계란, 세제 구매 부탁드립니다.",
  "category": "grocery",
  "budget_min": 15000,
  "budget_max": 25000,
  "due_at": "2026-03-20T10:00:00Z"
}
```

`ProposalResponse`

```json
{
  "id": 101,
  "title": "대형마트 장보기 대행",
  "description": "우유, 계란, 세제 구매 부탁드립니다.",
  "category": "grocery",
  "budget_min": 15000,
  "budget_max": 25000,
  "status": "open",
  "customer_id": 1,
  "offer_count": 2,
  "created_at": "2026-03-19T00:00:00Z"
}
```

### 4.3 Offer

`OfferCreateRequest`

```json
{
  "price": 22000,
  "message": "1시간 내 처리 가능합니다.",
  "eta_minutes": 60
}
```

`OfferResponse`

```json
{
  "id": 301,
  "proposal_id": 101,
  "runner_id": 7,
  "price": 22000,
  "message": "1시간 내 처리 가능합니다.",
  "eta_minutes": 60,
  "status": "pending",
  "created_at": "2026-03-19T00:05:00Z"
}
```

### 4.4 Mission

`MissionResponse`

```json
{
  "id": 501,
  "proposal_id": 101,
  "accepted_offer_id": 301,
  "customer_id": 1,
  "runner_id": 7,
  "status": "ready",
  "start_at": null,
  "complete_at": null,
  "created_at": "2026-03-19T00:06:00Z"
}
```

### 4.5 Payment

`PaymentResponse`

```json
{
  "id": 801,
  "mission_id": 501,
  "amount": 22000,
  "currency": "KRW",
  "status": "authorized",
  "provider": "mock-pg",
  "created_at": "2026-03-19T00:06:10Z"
}
```

## 5. 권한 정책

| 리소스 | 고객 | 수행자 | 관리자 |
| --- | --- | --- | --- |
| Proposal 생성 | 가능 | 가능 | 가능 |
| 내 Proposal 수정 | 가능 | 가능 | 가능 |
| 타인 Proposal 수정 | 불가 | 불가 | 가능 |
| Offer 생성 | 가능 | 가능 | 가능 |
| Offer 수락 | Proposal 작성자만 가능 | 불가 | 가능 |
| Mission 시작 | 불가 | 수행자만 가능 | 가능 |
| Mission 완료 | 불가 | 수행자만 가능 | 가능 |
| Payment 환불 | 불가 | 불가 | 관리자 또는 정책 엔진 |

초기 학습용 버전에서는 `customer`, `runner` 이중 역할이 가능할 수 있으므로 리소스 기준 권한 검사를 적용한다.

## 6. 검증 포인트

1. Proposal이 `open` 상태가 아니면 Offer 생성이 실패해야 한다.
2. 동일 사용자의 중복 Offer는 방지해야 한다.
3. Proposal 작성자가 아닌 사용자는 Offer를 수락할 수 없어야 한다.
4. Mission 상태 전이는 `ready -> in_progress -> completed` 순서를 따라야 한다.
5. Payment는 Mission 상태와 충돌하지 않아야 한다.

## 7. 현행 문서 불일치 리스크

기존 분석 로그 기준으로 Spring 프로젝트에는 문서 테스트 실패가 존재했다.

- 총 `31`개 테스트 중 `29`개 통과
- `ProposalControllerDocsTest` 계열 `2`개 실패

이 이력은 다음을 의미한다.

- 기존 응답 스펙과 실제 DTO 또는 문서 생성 규칙이 어긋났을 가능성이 높다.
- FastAPI 전환 시 OpenAPI 스키마를 코드 기반으로 관리해 문서-구현 괴리를 줄여야 한다.

## 8. 권장 Pydantic 모델 구성

| 모델 | 용도 |
| --- | --- |
| `UserProfileResponse` | 사용자 조회 응답 |
| `UserProfileUpdateRequest` | 사용자 수정 요청 |
| `ProposalCreateRequest` | 요청서 생성 |
| `ProposalUpdateRequest` | 요청서 수정 |
| `ProposalResponse` | 요청서 응답 |
| `OfferCreateRequest` | 제안 생성 |
| `OfferResponse` | 제안 응답 |
| `MissionResponse` | 미션 응답 |
| `PaymentResponse` | 결제 응답 |
| `ErrorResponse` | 공통 에러 응답 |
