# Offer API Spec

## API 목록
- `POST /v1/offer`: Offer 생성
- `GET /v1/offer?proposalId={id}`: Proposal에 연결된 Offer 목록 조회

---

## 성공 응답

### `POST /v1/offer`
Offer를 생성합니다.

**상태 코드**: `201 Created`

**요청 본문**:
```json
{
  "proposalId": 1,
  "runnerId": "runner-user-id",
  "estimatedTime": 30,
  "message": "30분 안에 가능합니다."
}
```

**필드 설명**:
- `proposalId` (required): Proposal ID (integer)
- `runnerId` (required): 러너 사용자 ID (string/integer)
- `estimatedTime` (required): 예상 수행 시간(분, 1 이상의 정수)
- `message` (optional): 제안 메시지 (최대 500자)

**응답 본문**:
```json
{
  "success": true,
  "data": {
    "id": 10,
    "proposalId": 1,
    "runnerId": "runner-user-id",
    "estimatedTime": 30,
    "message": "30분 안에 가능합니다.",
    "status": "WAITING",
    "createdAt": "2026-03-10T15:30:00"
  },
  "message": "제안이 제출되었습니다."
}
```

---

### `GET /v1/offer?proposalId={id}`
특정 Proposal에 연결된 모든 Offer를 조회합니다.

**상태 코드**: `200 OK`

**쿼리 파라미터**:
- `proposalId` (required): Offer를 조회할 Proposal ID

**응답 본문**:
```json
{
  "success": true,
  "data": [
    {
      "id": 11,
      "proposalId": 1,
      "runnerId": "runner-user-id",
      "estimatedTime": 25,
      "message": "25분 안에 가능합니다.",
      "status": "WAITING",
      "createdAt": "2026-03-10T15:35:00"
    },
    {
      "id": 10,
      "proposalId": 1,
      "runnerId": "another-runner-id",
      "estimatedTime": 30,
      "message": "30분 안에 가능합니다.",
      "status": "WAITING",
      "createdAt": "2026-03-10T15:30:00"
    }
  ],
  "message": "Success"
}
```

**참고**: 결과는 `createdAt` 기준 내림차순(최신순)으로 정렬됩니다.

---

## 실패 응답

### 유효성 검증 실패 (400 VALIDATION_ERROR)
- `proposalId` 누락
- `runnerId` 누락
- `estimatedTime < 1` (1 미만)
- `message` 길이 초과 (500자 초과)

**응답 예시**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력값이 유효하지 않습니다.",
    "details": {
      "estimatedTime": "1 이상이어야 합니다."
    }
  },
  "timestamp": "2026-03-10T15:30:00"
}
```

---

### 리소스 없음 (404 PROPOSAL_NOT_FOUND)
존재하지 않는 Proposal에 Offer를 생성하거나 조회한 경우

**응답 예시**:
```json
{
  "success": false,
  "error": {
    "code": "PROPOSAL_NOT_FOUND",
    "message": "요청을 찾을 수 없습니다.",
    "details": null
  },
  "timestamp": "2026-03-10T15:30:00"
}
```

---

### 도메인 예외

#### 중복 Offer 생성 (409 DUPLICATE_OFFER)
같은 Proposal에 같은 러너가 중복으로 Offer를 생성하는 경우

**응답 예시**:
```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_OFFER",
    "message": "이미 해당 요청에 제안을 제출했습니다.",
    "details": null
  },
  "timestamp": "2026-03-10T15:30:00"
}
```

#### Proposal 상태 불일치 (409 PROPOSAL_NOT_OPEN)
Proposal 상태가 `POSTED` 또는 `OFFERED`가 아닌 경우

**응답 예시**:
```json
{
  "success": false,
  "error": {
    "code": "PROPOSAL_NOT_OPEN",
    "message": "제안을 받을 수 없는 요청 상태입니다.",
    "details": null
  },
  "timestamp": "2026-03-10T15:30:00"
}
```

---

## 공통 에러 포맷
모든 에러 응답은 다음 구조를 따릅니다:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "사용자에게 표시할 메시지",
    "details": null | object
  },
  "timestamp": "2026-03-10T15:30:00"
}
```
