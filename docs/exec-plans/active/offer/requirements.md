# Offer Migration Requirements

## Current Policy

- Offer는 러너가 특정 Proposal에 수행 의사를 제출하는 Bidding 도메인이다.
- 모든 Offer API는 JWT 인증이 필요하다.
- 현재 Offer 생성 요청은 `proposalId`만 받는다.
- 현재 Offer 응답은 `id`, `proposalId`, `runnerId`, `runnerName`, `status`, `createdAt`을 반환한다.
- 같은 Proposal에 같은 러너는 하나의 Offer만 생성할 수 있다.
- Offer 수락은 Mission 생성과 Proposal/Offer 상태 전이를 함께 수행한다.

## Target Policy

- FastAPI 구현은 현재 Java 구현과 같은 요청/응답/상태 코드/메시지/상태 전이를 유지한다.
- Proposal migration 결과를 재사용한다.
- Mission 자체 API는 다음 도메인에서 다루되, Offer 수락으로 Mission을 생성하는 orchestration은 Offer migration 범위에 포함한다.

## In Scope

- `POST /v1/offer`
- `POST /v1/offer/{offerId}/accept`
- `GET /v1/offer/{offerId}`
- `GET /v1/offer?proposalId={id}`
- `GET /v1/offer/own`
- `DELETE /v1/offer/{offerId}`
- `OfferStatus`
- Proposal 상태 연동
- Offer 수락 시 Mission 생성
- Offer 취소와 권한 검증

## Out Of Scope

- Offer 수정 API
- 금액/예상 시간/메시지를 포함한 입찰 조건
- Mission 상태 업데이트 API
- Settlement/Payment 생성

## Acceptance Criteria

### `POST /v1/offer`

- 인증된 사용자는 별도 역할 없이 Offer를 생성할 수 있다.
- `proposalId`는 필수이며 1 이상이어야 한다.
- 존재하지 않는 Proposal이면 404 `PROPOSAL_NOT_FOUND`다.
- Proposal 상태가 `POSTED` 또는 `OFFERED`가 아니면 409 `PROPOSAL_NOT_OPEN`이다.
- 같은 `proposalId + runnerId` 중복이면 409 `DUPLICATE_OFFER`다.
- 성공 시 201 Created, 메시지 `제안이 제출되었습니다.`를 반환한다.
- 성공 시 Offer 상태는 `WAITING`이다.
- Proposal이 `POSTED`였으면 `OFFERED`로 전이한다.

### `POST /v1/offer/{offerId}/accept`

- 연결 Proposal 작성자만 호출할 수 있다.
- 요청 본문은 받지 않는다.
- Offer가 없으면 404 `OFFER_NOT_FOUND`다.
- 요청자가 Proposal 작성자가 아니면 403 `FORBIDDEN`이다.
- 이미 Mission이 있으면 409 `MISSION_ALREADY_EXISTS`다.
- Offer 상태가 `WAITING`이 아니면 409 `OFFER_NOT_ACCEPTABLE`이다.
- Proposal 상태가 `OFFERED`가 아니면 409 `PROPOSAL_NOT_MATCHABLE`이다.
- 성공 시 Mission이 `CREATED`로 생성된다.
- 수락된 Offer는 `ACCEPTED`가 된다.
- 같은 Proposal의 다른 `WAITING` Offer는 `REJECTED`가 된다.
- Proposal은 `MATCHED`가 된다.
- 성공 메시지는 `제안이 수락되었습니다.`다.

### `GET /v1/offer/{offerId}`

- Offer 제출자 본인은 조회할 수 있다.
- 연결 Proposal 작성자는 조회할 수 있다.
- 그 외 사용자는 403 `FORBIDDEN`이다.
- Offer가 없으면 404 `OFFER_NOT_FOUND`다.

### `GET /v1/offer?proposalId={id}`

- `proposalId`는 필수다.
- Proposal이 없으면 404 `PROPOSAL_NOT_FOUND`다.
- Offer가 없으면 빈 배열을 반환한다.
- 목록은 `createdAt` 내림차순이다.

### `GET /v1/offer/own`

- 현재 사용자가 runner인 Offer만 반환한다.
- `status` 쿼리가 있으면 해당 상태만 반환한다.
- 응답은 PageResponse다.

### `DELETE /v1/offer/{offerId}`

- Offer 제출자 본인만 취소할 수 있다.
- `WAITING` 상태만 취소할 수 있다.
- 성공 시 204 No Content이며 응답 본문은 없다.
- Offer가 없으면 404 `OFFER_NOT_FOUND`다.
- 제출자가 아니면 403 `FORBIDDEN`이다.
- 취소 불가능 상태면 409 `OFFER_NOT_CANCELLABLE`이다.
