# Offer Integration Test Plan

## 정상 시나리오

### 생성 성공

- 엔드포인트: `POST /v1/offer`
- 요청: `{ "proposalId": 1 }`
- 검증:
  - 201 Created
  - `ApiResponse` 구조
  - 응답에 `id`, `proposalId`, `runnerId`, `runnerName`, `status`, `createdAt` 포함
  - 저장된 Offer 상태는 `WAITING`
  - Proposal이 `POSTED`였으면 `OFFERED`로 전이

### 목록 조회 성공

- 엔드포인트: `GET /v1/offer?proposalId={id}`
- 검증:
  - 200 OK
  - 같은 Proposal의 Offer만 반환
  - `createdAt` 내림차순
  - Offer가 없으면 빈 배열

### 상세 조회 성공

- 엔드포인트: `GET /v1/offer/{offerId}`
- 검증:
  - Offer 제출자 본인과 Proposal 작성자는 200 OK
  - 그 외 사용자는 403 `FORBIDDEN`

### 내 목록 조회 성공

- 엔드포인트: `GET /v1/offer/own`
- 검증:
  - 현재 runner 기준 Offer만 반환
  - `status` 필터 동작
  - PageResponse 구조

### 수락 성공

- 엔드포인트: `POST /v1/offer/{offerId}/accept`
- 요청: 본문 없음
- 검증:
  - Mission `CREATED` 생성
  - 선택 Offer `ACCEPTED`
  - 같은 Proposal의 다른 `WAITING` Offer `REJECTED`
  - Proposal `MATCHED`

### 취소 성공

- 엔드포인트: `DELETE /v1/offer/{offerId}`
- 검증:
  - 본인 `WAITING` Offer는 204 No Content
  - DB 상태는 `CANCELLED`

## 실패 시나리오

- 토큰 없음: 401 `INVALID_TOKEN`
- `proposalId` 누락 또는 1 미만: 400 `VALIDATION_ERROR`
- 없는 Proposal: 404 `PROPOSAL_NOT_FOUND`
- 없는 Offer: 404 `OFFER_NOT_FOUND`
- 중복 생성: 409 `DUPLICATE_OFFER`
- 생성 불가능 Proposal 상태: 409 `PROPOSAL_NOT_OPEN`
- 상세/수락/취소 권한 없음: 403 `FORBIDDEN`
- 수락 불가능 Offer 상태: 409 `OFFER_NOT_ACCEPTABLE`
- 매칭 불가능 Proposal 상태: 409 `PROPOSAL_NOT_MATCHABLE`
- 기존 Mission 존재: 409 `MISSION_ALREADY_EXISTS`
- 취소 불가능 Offer 상태: 409 `OFFER_NOT_CANCELLABLE`
