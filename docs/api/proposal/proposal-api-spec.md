# Proposal API Specification

## Base Path
`/api/v1/proposal`

## Authentication
- POST 요청은 JWT Bearer 인증 필요
- GET 요청은 인증 불필요 (공개 정보)

---

## 1. GET /api/v1/proposal

### 설명
전체 제안 목록을 조회합니다.

### 요청
```http
GET /api/v1/proposal HTTP/1.1
```

#### Query Parameters (추후 확장 예정)
- `status`: 상태 필터링 (옵션)
- `page`: 페이지 번호 (옵션, 기본값: 1)
- `size`: 페이지 크기 (옵션, 기본값: 20)

### 응답

#### 성공 (200 OK)
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "ordererId": 10,
      "title": "강남역에서 커피 배달",
      "content": "스타벅스 아메리카노 아이스 2잔",
      "deadline": "2026-03-27T15:00:00+09:00",
      "errandFee": 5000,
      "status": "POSTED",
      "createdAt": "2026-03-27T10:30:00+09:00",
      "updatedAt": "2026-03-27T10:30:00+09:00"
    }
  ]
}
```

---

## 2. GET /api/v1/proposal/{id}

### 설명
특정 제안의 상세 정보를 조회합니다.

### 요청
```http
GET /api/v1/proposal/1 HTTP/1.1
```

#### Path Parameters
- `id` (required): Proposal ID (정수)

### 응답

#### 성공 (200 OK)
```json
{
  "success": true,
  "data": {
    "id": 1,
    "ordererId": 10,
    "title": "강남역에서 커피 배달",
    "content": "스타벅스 아메리카노 아이스 2잔 부탁드립니다. 건물 입구에서 전달해주세요.",
    "deadline": "2026-03-27T15:00:00+09:00",
    "errandFee": 5000,
    "status": "POSTED",
    "createdAt": "2026-03-27T10:30:00+09:00",
    "updatedAt": "2026-03-27T10:30:00+09:00"
  }
}
```

#### 실패 (404 Not Found)
```json
{
  "success": false,
  "error": {
    "code": "PROPOSAL_NOT_FOUND",
    "message": "제안을 찾을 수 없습니다.",
    "details": "id: 999"
  },
  "timestamp": "2026-03-27T12:00:00+09:00"
}
```

---

## 3. POST /api/v1/proposal

### 설명
새로운 제안을 생성합니다.

### 인증
**Required**: Bearer Token

### 요청
```http
POST /api/v1/proposal HTTP/1.1
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "강남역에서 커피 배달",
  "content": "스타벅스 아메리카노 아이스 2잔 부탁드립니다.",
  "deadline": "2026-03-27T15:00:00+09:00",
  "errandFee": 5000
}
```

#### Request Body
| 필드 | 타입 | 필수 | 제약 | 설명 |
|------|------|------|------|------|
| `title` | string | O | 1-50자 | 제목 |
| `content` | string | O | 1-500자 | 내용 |
| `deadline` | datetime | O | 미래 시각 | 완료 희망 시각 |
| `errandFee` | integer | O | >= 0 | 심부름비 (원) |

### 응답

#### 성공 (201 Created)
```json
{
  "success": true,
  "data": {
    "id": 1,
    "ordererId": 10,
    "title": "강남역에서 커피 배달",
    "content": "스타벅스 아메리카노 아이스 2잔 부탁드립니다.",
    "deadline": "2026-03-27T15:00:00+09:00",
    "errandFee": 5000,
    "status": "POSTED",
    "createdAt": "2026-03-27T10:30:00+09:00",
    "updatedAt": "2026-03-27T10:30:00+09:00"
  }
}
```

#### 실패 - 유효성 검증 실패 (400 Bad Request)
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "요청 값이 올바르지 않습니다.",
    "details": "title: 제목은 50자를 초과할 수 없습니다"
  },
  "timestamp": "2026-03-27T12:00:00+09:00"
}
```

##### 유효성 검증 규칙
- **title**
  - 필수 값
  - 1자 이상 50자 이하

- **content**
  - 필수 값
  - 1자 이상 500자 이하

- **deadline**
  - 필수 값
  - 현재 시각보다 미래여야 함
  - ISO 8601 형식

- **errandFee**
  - 필수 값
  - 0 이상의 정수

#### 실패 - 인증 실패 (401 Unauthorized)
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증이 필요합니다.",
    "details": null
  },
  "timestamp": "2026-03-27T12:00:00+09:00"
}
```

---

## 공통 에러 코드

| 코드 | HTTP 상태 | 설명 |
|------|-----------|------|
| `VALIDATION_ERROR` | 400 | 요청 값 검증 실패 |
| `UNAUTHORIZED` | 401 | 인증 실패 |
| `PROPOSAL_NOT_FOUND` | 404 | 제안을 찾을 수 없음 |
| `INTERNAL_SERVER_ERROR` | 500 | 서버 내부 오류 |

---

## Response Schema

### ApiResponse<T>
```typescript
{
  "success": boolean,
  "data": T | null,
  "timestamp": string // ISO 8601
}
```

### ErrorResponse
```typescript
{
  "success": false,
  "error": {
    "code": string,
    "message": string,
    "details": string | null
  },
  "timestamp": string // ISO 8601
}
```

### ProposalResponse
```typescript
{
  "id": number,
  "ordererId": number,
  "title": string,
  "content": string,
  "deadline": string, // ISO 8601
  "errandFee": number,
  "status": "POSTED" | "OFFERED" | "MATCHED" | "CANCELLED",
  "createdAt": string, // ISO 8601
  "updatedAt": string  // ISO 8601
}
```
