# Mission API Specification

## Base Path
`/api/v1`

## Authentication
- All endpoints require JWT Bearer authentication

---

## 1. POST /api/v1/offer/{offer_id}/accept

### 설명
오도러가 특정 러너의 Offer를 수락하여 Mission을 생성합니다.

**동작:**
1. Offer와 Proposal 유효성 검증
2. Mission 생성 (계약 금액 스냅샷 저장)
3. 수락된 Offer → `ACCEPTED` 상태로 변경
4. Proposal → `MATCHED` 상태로 변경
5. 동일 Proposal의 다른 대기 중인 Offer들 → `REJECTED` 상태로 변경

### 인증
**Required**: Bearer Token (오도러만 가능)

### 요청
```http
POST /api/v1/offer/123/accept HTTP/1.1
Authorization: Bearer {access_token}
```

#### Path Parameters
- `offer_id` (required): 수락할 Offer ID (정수)

### 응답

#### 성공 (201 Created)
```json
{
  "success": true,
  "data": {
    "id": 1,
    "proposalId": 10,
    "offerId": 123,
    "ordererId": 5,
    "runnerId": 15,
    "contractAmount": 10000,
    "status": "CREATED",
    "deliveryProofImageUrl": null,
    "disputeReason": null,
    "createdAt": "2026-03-29T12:00:00+09:00",
    "startedAt": null,
    "completedAt": null,
    "settledAt": null,
    "updatedAt": "2026-03-29T12:00:00+09:00"
  },
  "message": "제안이 수락되어 미션이 생성되었습니다."
}
```

#### 실패 - 인증 실패 (401 Unauthorized)
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증이 필요합니다.",
    "details": null
  },
  "timestamp": "2026-03-29T12:00:00+09:00"
}
```

#### 실패 - 권한 없음 (403 Forbidden)
Proposal의 오도러가 아닌 사용자가 Offer를 수락하려는 경우

```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "본인의 요청에 대한 제안만 수락할 수 있습니다.",
    "details": null
  },
  "timestamp": "2026-03-29T12:00:00+09:00"
}
```

#### 실패 - Offer 없음 (404 Not Found)
```json
{
  "success": false,
  "error": {
    "code": "OFFER_NOT_FOUND",
    "message": "제안을 찾을 수 없습니다.",
    "details": null
  },
  "timestamp": "2026-03-29T12:00:00+09:00"
}
```

#### 실패 - Proposal 없음 (404 Not Found)
```json
{
  "success": false,
  "error": {
    "code": "PROPOSAL_NOT_FOUND",
    "message": "요청을 찾을 수 없습니다.",
    "details": null
  },
  "timestamp": "2026-03-29T12:00:00+09:00"
}
```

#### 실패 - 잘못된 Offer 상태 (400 Bad Request)
이미 수락/거절된 Offer를 수락하려는 경우

```json
{
  "success": false,
  "error": {
    "code": "INVALID_OFFER_STATUS",
    "message": "이미 처리된 제안입니다.",
    "details": null
  },
  "timestamp": "2026-03-29T12:00:00+09:00"
}
```

#### 실패 - 잘못된 Proposal 상태 (400 Bad Request)
Proposal이 OFFERED 상태가 아닌 경우

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PROPOSAL_STATUS",
    "message": "제안을 받을 수 없는 요청 상태입니다.",
    "details": null
  },
  "timestamp": "2026-03-29T12:00:00+09:00"
}
```

---

## Mission Status Flow

Mission은 다음과 같은 상태 흐름을 가집니다:

```
CREATED (매칭)
    ↓
IN_PROGRESS (배달 중)
    ↓
DELIVERY_COMPLETED (전달 완료)
    ↓
RECEIVED_CONFIRMED (수령 확인)
    ↓
SETTLED (정산 완료)
```

**분쟁 처리 흐름:**
```
DELIVERY_COMPLETED or RECEIVED_CONFIRMED
    ↓
DISPUTED (분쟁)
    ↓
SETTLED or REFUNDED
```

---

## Response Schema

### MissionResponse
```typescript
{
  "id": number,
  "proposalId": number,
  "offerId": number,
  "ordererId": number,
  "runnerId": number,
  "contractAmount": number,  // Snapshot of errand_fee at mission creation
  "status": "CREATED" | "IN_PROGRESS" | "DELIVERY_COMPLETED" | "RECEIVED_CONFIRMED" | "SETTLED" | "DISPUTED" | "REFUNDED",
  "deliveryProofImageUrl": string | null,
  "disputeReason": string | null,
  "createdAt": string,  // ISO 8601
  "startedAt": string | null,  // ISO 8601
  "completedAt": string | null,  // ISO 8601
  "settledAt": string | null,  // ISO 8601
  "updatedAt": string  // ISO 8601
}
```

---

## 공통 에러 코드

| 코드 | HTTP 상태 | 설명 |
|------|-----------|------|
| `UNAUTHORIZED` | 401 | 인증 실패 |
| `FORBIDDEN` | 403 | 권한 없음 (오도러가 아님) |
| `OFFER_NOT_FOUND` | 404 | Offer를 찾을 수 없음 |
| `PROPOSAL_NOT_FOUND` | 404 | Proposal을 찾을 수 없음 |
| `INVALID_OFFER_STATUS` | 400 | 잘못된 Offer 상태 |
| `INVALID_PROPOSAL_STATUS` | 400 | 잘못된 Proposal 상태 |
| `INTERNAL_SERVER_ERROR` | 500 | 서버 내부 오류 |

---

## 비즈니스 규칙

1. **계약 금액 불변성**: Mission 생성 시 Proposal의 `errand_fee`를 `contract_amount`로 스냅샷 저장하여 이후 변경 불가
2. **Offer 배타성**: 하나의 Offer만 수락 가능하며, 수락 시 다른 대기 중인 Offer는 자동으로 거절
3. **Proposal 상태 전이**: Offer 수락 시 Proposal은 `OFFERED` → `MATCHED`로 전이
4. **권한 검증**: Proposal의 오도러만 해당 Proposal에 대한 Offer를 수락 가능
5. **에스크로**: Proposal 입금 확인된 금액(`errand_fee`)을 Mission 에스크로로 사용
