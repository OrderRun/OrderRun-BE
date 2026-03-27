# Offer Integration Test Plan

## 정상 시나리오

### 생성 성공
- **엔드포인트**: `POST /v1/offer`
- **설명**: `proposalId`, `runnerId`, `estimatedTime`, `message`를 전송하면 `201 Created`를 반환
- **검증 포인트**:
  - HTTP 상태 코드 201
  - 응답 구조가 `ApiResponse` 형식
  - 저장된 Offer 상태는 `WAITING`
  - DB에 실제로 저장되었는지 확인
  - 응답에 `runnerId`가 포함되는지 확인

### 첫 Offer 생성 시 Proposal 상태 변경
- **설명**: 첫 Offer 생성 시 Proposal 상태가 `POSTED` → `OFFERED`로 변경
- **검증 포인트**:
  - Proposal 상태가 `OFFERED`로 변경되었는지 확인
  - 두 번째 Offer 생성 시에는 Proposal 상태가 변경되지 않음

### 목록 조회 성공
- **엔드포인트**: `GET /v1/offer?proposalId={id}`
- **설명**: 같은 Proposal에 연결된 Offer 전체를 최신 생성 순으로 반환
- **검증 포인트**:
  - HTTP 상태 코드 200
  - 응답 구조가 `ApiResponse` 형식
  - 조회 결과가 `createdAt` 기준 내림차순(최신순)인지 확인
  - 같은 Proposal의 Offer만 반환되는지 확인

### 빈 목록 조회 성공
- **설명**: Proposal은 존재하지만 Offer가 없는 경우 빈 배열 반환
- **검증 포인트**:
  - HTTP 상태 코드 200
  - 빈 배열 `[]`을 반환하는지 확인

---

## 실패 시나리오

### 필수값 누락
- **설명**: `proposalId`, `runnerId`, `estimatedTime` 누락 시 `400 VALIDATION_ERROR`
- **검증 포인트**:
  - HTTP 상태 코드 400
  - `ErrorResponse` 구조
  - `code`가 `VALIDATION_ERROR`
  - `message`에 어떤 필드가 누락되었는지 명시

### 길이 제한 초과
- **설명**: `message`가 500자를 넘으면 `400 VALIDATION_ERROR`
- **검증 포인트**:
  - HTTP 상태 코드 400
  - `ErrorResponse` 구조
  - `code`가 `VALIDATION_ERROR`
  - `details`에 `message` 필드 관련 에러 정보

### estimatedTime 범위 초과
- **설명**: `estimatedTime < 1`인 경우 `400 VALIDATION_ERROR`
- **검증 포인트**:
  - HTTP 상태 코드 400
  - `ErrorResponse` 구조
  - `code`가 `VALIDATION_ERROR`
  - `details`에 `estimatedTime` 필드 관련 에러 정보

### 도메인 규칙 위반: 중복 생성
- **설명**: 같은 `proposalId + runnerId` 중복 생성 시 `409 DUPLICATE_OFFER`
- **검증 포인트**:
  - HTTP 상태 코드 409
  - `ErrorResponse` 구조
  - `code`가 `DUPLICATE_OFFER`
  - DB에 중복 데이터가 생성되지 않았는지 확인

### 도메인 규칙 위반: Proposal 상태 불일치
- **설명**: Proposal 상태가 `MATCHED`, `CANCELLED` 등이면 `409 PROPOSAL_NOT_OPEN`
- **검증 포인트**:
  - HTTP 상태 코드 409
  - `ErrorResponse` 구조
  - `code`가 `PROPOSAL_NOT_OPEN`
  - DB에 Offer가 생성되지 않았는지 확인

### 없는 리소스 조회
- **설명**: 존재하지 않는 Proposal에 생성/조회 시 `404 PROPOSAL_NOT_FOUND`
- **검증 포인트**:
  - HTTP 상태 코드 404
  - `ErrorResponse` 구조
  - `code`가 `PROPOSAL_NOT_FOUND`

---

## 검증 포인트 체크리스트

### HTTP 응답
- [ ] 올바른 HTTP 상태 코드 반환
- [ ] `ApiResponse`, `ErrorResponse` 구조 준수
- [ ] `success` 필드 값이 올바른지

### 데이터 정합성
- [ ] DB 저장/조회 정합성
- [ ] 상태 전이와 기본값이 올바른지
- [ ] `runnerId`가 응답에 포함되는지

### 정렬 및 필터링
- [ ] 조회 결과가 `createdAt` 기준 내림차순인지
- [ ] 같은 Proposal의 Offer만 조회되는지

### 비즈니스 로직
- [ ] 첫 Offer 생성 시 Proposal 상태가 `OFFERED`로 변경
- [ ] 중복 생성 방지
- [ ] Proposal 상태에 따른 생성 가능 여부 검증

### 에러 처리
- [ ] 에러 코드가 올바른지
- [ ] 에러 메시지가 명확한지
- [ ] `details` 필드에 필요한 정보가 포함되는지
