# Offer API Spec

## API 목록

- `POST /v1/offer`: Offer 생성
- `POST /v1/offer/{offerId}/accept`: Offer 수락 및 Mission 생성
- `GET /v1/offer/{offerId}`: Offer 상세 조회
- `GET /v1/offer?proposalId={id}`: Proposal에 연결된 Offer 목록 조회
- `GET /v1/offer/own`: 현재 러너의 Offer 목록 조회
- `DELETE /v1/offer/{offerId}`: Offer 취소

## 공통

- 모든 Offer API는 JWT Bearer 인증이 필요하다.
- 성공 응답은 `ApiResponse`로 감싼다. 단, 취소 성공은 `204 No Content`와 빈 본문을 반환한다.
- 에러 응답은 `ErrorResponse` 형식이다.

## `POST /v1/offer`

Offer를 생성합니다.

**상태 코드**: `201 Created`

**요청 본문**:

```json
{
  "proposalId": 1
}
```

**응답 본문**:

```json
{
  "success": true,
  "data": {
    "id": 10,
    "proposalId": 1,
    "runnerId": "runner-user-id",
    "runnerName": "홍길동",
    "status": "WAITING",
    "createdAt": "2026-03-10T15:30:00"
  },
  "message": "제안이 제출되었습니다."
}
```

## `POST /v1/offer/{offerId}/accept`

Proposal 작성자가 Offer를 수락하고 Mission을 생성합니다.

**요청 본문**:

```json
{
  "runFee": 3000,
  "itemPrice": 2000
}
```

**응답 본문**:

```json
{
  "success": true,
  "data": {
    "proposalId": 1,
    "offerId": 10,
    "missionId": 7,
    "proposalStatus": "MATCHED",
    "acceptedOfferStatus": "ACCEPTED",
    "rejectedOfferCount": 1,
    "missionStatus": "CREATED",
    "ordererId": "orderer-user-id",
    "runnerId": "runner-user-id",
    "runFee": 3000,
    "itemPrice": 2000,
    "totalAmount": 5000,
    "createdAt": "2026-03-10T15:30:00"
  },
  "message": "제안이 수락되었습니다."
}
```

## `GET /v1/offer/{offerId}`

Offer 제출자 본인 또는 연결 Proposal 작성자가 Offer를 조회합니다.

## `GET /v1/offer?proposalId={id}`

특정 Proposal에 연결된 모든 Offer를 `createdAt` 내림차순으로 조회합니다.

## `GET /v1/offer/own`

현재 사용자가 runner인 Offer를 PageResponse로 조회합니다.

Query:

- `status` optional: `WAITING`, `ACCEPTED`, `COMPLETED`, `REJECTED`, `CANCELLED`
- `page` optional, default `1`
- `size` optional, default `20`, max `100`

## `DELETE /v1/offer/{offerId}`

Offer 제출자 본인이 `WAITING` Offer를 취소합니다.

**상태 코드**: `204 No Content`

## 주요 에러

| Code | HTTP | 조건 |
| --- | --- | --- |
| `INVALID_TOKEN` | 401 | 토큰 없음 또는 유효하지 않음 |
| `VALIDATION_ERROR` | 400 | 요청 필드 누락 또는 범위 오류 |
| `SELF_OFFER_NOT_ALLOWED` | 400 | Proposal 작성자가 본인 Proposal에 Offer 생성 |
| `PROPOSAL_NOT_FOUND` | 404 | Proposal 없음 |
| `OFFER_NOT_FOUND` | 404 | Offer 없음 |
| `FORBIDDEN` | 403 | 상세/수락/취소 권한 없음 |
| `DUPLICATE_OFFER` | 409 | 같은 Proposal에 같은 runner가 중복 생성 |
| `PROPOSAL_NOT_OPEN` | 409 | Proposal이 `POSTED`/`OFFERED`가 아님 |
| `MISSION_ALREADY_EXISTS` | 409 | 이미 Mission 존재 |
| `OFFER_NOT_ACCEPTABLE` | 409 | Offer가 `WAITING`이 아님 |
| `PROPOSAL_NOT_MATCHABLE` | 409 | Proposal이 `OFFERED`가 아님 |
| `OFFER_NOT_CANCELLABLE` | 409 | Offer가 `WAITING`이 아님 |
