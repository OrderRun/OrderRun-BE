# Proposal Integration Test Plan

## 테스트 목표
Proposal API의 전체 흐름과 비즈니스 규칙을 검증합니다.

## 테스트 환경
- MySQL 테스트 데이터베이스
- FastAPI TestClient
- Mock OAuth (실제 인증 서버 불필요)
- 각 테스트는 독립적으로 실행 (DB 초기화)

---

## 1. 정상 시나리오

### 1.1 전체 제안 목록 조회 성공
**Given**: 데이터베이스에 여러 Proposal이 존재
**When**: `GET /api/v1/proposal` 호출
**Then**:
- HTTP 상태 코드 200
- `success: true`
- `data` 배열에 모든 Proposal 포함
- 각 항목에 필수 필드 존재 (`id`, `title`, `content`, `deadline`, `errandFee`, `status`)

### 1.2 빈 목록 조회 성공
**Given**: 데이터베이스에 Proposal이 없음
**When**: `GET /api/v1/proposal` 호출
**Then**:
- HTTP 상태 코드 200
- `success: true`
- `data` 배열이 비어있음 (`[]`)

### 1.3 상세 제안 조회 성공
**Given**: ID가 1인 Proposal이 존재
**When**: `GET /api/v1/proposal/1` 호출
**Then**:
- HTTP 상태 코드 200
- `success: true`
- `data` 객체에 해당 Proposal의 모든 정보 포함
- `ordererId`, `title`, `content`, `deadline`, `errandFee`, `status`, `createdAt`, `updatedAt` 검증

### 1.4 제안 생성 성공
**Given**: 인증된 사용자
**When**: 유효한 데이터로 `POST /api/v1/proposal` 호출
```json
{
  "title": "강남역에서 커피 배달",
  "content": "스타벅스 아메리카노 아이스 2잔",
  "deadline": "2026-03-28T15:00:00+09:00",
  "errandFee": 5000
}
```
**Then**:
- HTTP 상태 코드 201
- `success: true`
- `data.id` 존재 (자동 생성)
- `data.ordererId` == 인증된 사용자 ID
- `data.status` == "POSTED"
- `data.createdAt`, `data.updatedAt` 자동 설정
- DB에 실제로 저장되었는지 검증

---

## 2. 실패 시나리오

### 2.1 제목 길이 초과 (51자)
**Given**: 인증된 사용자
**When**: 제목이 51자인 데이터로 `POST /api/v1/proposal` 호출
**Then**:
- HTTP 상태 코드 400
- `success: false`
- `error.code` == "VALIDATION_ERROR"
- `error.message` 포함
- `error.details`에 "title" 관련 메시지 포함

### 2.2 제목 빈 문자열
**Given**: 인증된 사용자
**When**: 제목이 빈 문자열인 데이터로 `POST /api/v1/proposal` 호출
**Then**:
- HTTP 상태 코드 400
- `success: false`
- `error.code` == "VALIDATION_ERROR"

### 2.3 내용 길이 초과 (501자)
**Given**: 인증된 사용자
**When**: 내용이 501자인 데이터로 `POST /api/v1/proposal` 호출
**Then**:
- HTTP 상태 코드 400
- `success: false`
- `error.code` == "VALIDATION_ERROR"
- `error.details`에 "content" 관련 메시지 포함

### 2.4 내용 빈 문자열
**Given**: 인증된 사용자
**When**: 내용이 빈 문자열인 데이터로 `POST /api/v1/proposal` 호출
**Then**:
- HTTP 상태 코드 400
- `success: false`
- `error.code` == "VALIDATION_ERROR"

### 2.5 데드라인 과거 시각
**Given**: 인증된 사용자
**When**: 데드라인이 현재 시각보다 과거인 데이터로 `POST /api/v1/proposal` 호출
```json
{
  "deadline": "2020-01-01T10:00:00+09:00"
}
```
**Then**:
- HTTP 상태 코드 400
- `success: false`
- `error.code` == "VALIDATION_ERROR"
- `error.details`에 "deadline" 관련 메시지 포함

### 2.6 심부름비 음수
**Given**: 인증된 사용자
**When**: 심부름비가 음수인 데이터로 `POST /api/v1/proposal` 호출
```json
{
  "errandFee": -1000
}
```
**Then**:
- HTTP 상태 코드 400
- `success: false`
- `error.code` == "VALIDATION_ERROR"
- `error.details`에 "errandFee" 관련 메시지 포함

### 2.7 심부름비 0 (경계값 - 성공해야 함)
**Given**: 인증된 사용자
**When**: 심부름비가 0인 데이터로 `POST /api/v1/proposal` 호출
**Then**:
- HTTP 상태 코드 201
- `success: true`
- `data.errandFee` == 0

### 2.8 없는 제안 상세 조회
**Given**: ID가 9999인 Proposal이 존재하지 않음
**When**: `GET /api/v1/proposal/9999` 호출
**Then**:
- HTTP 상태 코드 404
- `success: false`
- `error.code` == "PROPOSAL_NOT_FOUND"
- `error.message` 포함

### 2.9 인증 없이 제안 생성 시도
**Given**: 인증되지 않은 사용자 (토큰 없음)
**When**: `POST /api/v1/proposal` 호출
**Then**:
- HTTP 상태 코드 401
- `success: false`
- `error.code` == "UNAUTHORIZED" 또는 인증 관련 에러

### 2.10 잘못된 토큰으로 제안 생성 시도
**Given**: 유효하지 않은 토큰
**When**: `POST /api/v1/proposal` 호출
**Then**:
- HTTP 상태 코드 401
- `success: false`

---

## 3. 검증 포인트

### 3.1 HTTP 상태 코드
- 성공: 200 (조회), 201 (생성)
- 클라이언트 에러: 400 (유효성 검증), 401 (인증), 404 (Not Found)
- 서버 에러: 500

### 3.2 응답 구조
#### 성공 응답
```json
{
  "success": true,
  "data": {...} 또는 [...]
}
```

#### 에러 응답
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지",
    "details": "상세 정보 또는 null"
  },
  "timestamp": "ISO 8601 형식"
}
```

### 3.3 생성 후 DB 저장 검증
- DB에서 생성된 Proposal을 다시 조회
- 모든 필드 값 일치 확인
- `created_at`, `updated_at` 자동 설정 확인
- 기본 상태 `POSTED` 확인

### 3.4 Proposal 기본 상태
- 생성 직후 `status`는 항상 `POSTED`
- 다른 상태로 생성 불가

### 3.5 필드 타입 검증
- `id`: 정수
- `ordererId`: 정수
- `title`: 문자열
- `content`: 문자열
- `deadline`: ISO 8601 datetime 문자열
- `errandFee`: 정수
- `status`: 문자열 (enum)
- `createdAt`, `updatedAt`: ISO 8601 datetime 문자열

### 3.6 타임스탬프 검증
- `createdAt`은 요청 시각과 근사해야 함 (±5초)
- 생성 직후 `createdAt` == `updatedAt`
- 모든 datetime은 ISO 8601 형식 (+09:00 타임존 포함)

---

## 4. 테스트 데이터 준비

### 4.1 샘플 사용자
```python
sample_user = User(
    email="orderer@example.com",
    nickname="테스트주문자",
    role=UserRole.CUSTOMER,
    status=UserStatus.ACTIVE,
    oauth_provider=OAuthProvider.KAKAO,
    oauth_id="test_orderer_123"
)
```

### 4.2 유효한 Proposal 데이터
```python
valid_proposal_data = {
    "title": "강남역에서 커피 배달",
    "content": "스타벅스 아메리카노 아이스 2잔 부탁드립니다.",
    "deadline": (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat(),
    "errandFee": 5000
}
```

### 4.3 경계값 테스트 데이터
```python
# 제목 50자 (최대 허용)
max_title = "가" * 50

# 제목 51자 (초과)
over_title = "가" * 51

# 내용 500자 (최대 허용)
max_content = "가" * 500

# 내용 501자 (초과)
over_content = "가" * 501

# 심부름비 0 (최소 허용)
min_fee = 0

# 심부름비 -1 (불허)
negative_fee = -1
```

---

## 5. 테스트 실행 순서

1. 전체 목록 조회 (빈 목록)
2. 제안 생성 성공
3. 전체 목록 조회 (1개 존재)
4. 상세 조회 성공
5. 유효성 검증 실패 케이스들
6. 없는 제안 조회 실패
7. 인증 실패 케이스들

---

## 6. Mock 설정

### 6.1 인증 Mock
- JWT 토큰을 실제로 생성하여 사용
- `auth_headers` fixture 사용

### 6.2 시간 Mock (선택사항)
- 데드라인 검증을 위해 `freezegun` 또는 동적 시간 생성 사용
- 현재 시각보다 미래인 값을 동적으로 생성

---

## 7. 커버리지 목표

- 라인 커버리지: 80% 이상
- 브랜치 커버리지: 75% 이상
- 모든 API 엔드포인트: 100%
- 모든 유효성 검증 규칙: 100%
