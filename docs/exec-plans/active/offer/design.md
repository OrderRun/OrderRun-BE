# Offer Migration Design

## Decision

- Offer는 Proposal에 종속된 Bidding aggregate로 구현한다.
- 현재 Java API와 동일하게 Offer 생성 입력은 `proposalId`만 받는다.
- Offer 수락은 Mission 생성, Proposal 상태 전이, Offer 상태 전이를 하나의 트랜잭션으로 처리한다.
- 권한 검사는 current user id와 Offer runner/proposal orderer 비교로 수행한다.

## Responsibilities

### API Layer

- endpoint binding, request validation, response wrapping을 담당한다.
- 생성/수락/조회는 `ApiResponse`를 사용한다.
- 내 목록은 `PageResponse`를 사용한다.
- 취소 성공은 204 No Content로 응답한다.

### Offer Service

- 생성 시 Proposal 존재와 상태를 검증한다.
- 중복 Offer를 차단한다.
- runner 사용자 존재를 검증하고 Offer를 `WAITING`으로 저장한다.
- Proposal이 `POSTED`면 `OFFERED`로 전이한다.
- 상세 조회와 취소의 사용자 권한을 검증한다.

### Offer Acceptance Service

- Offer 존재와 Proposal 작성자 권한을 검증한다.
- 중복 Mission 생성을 차단한다.
- Offer가 `WAITING`, Proposal이 `OFFERED`인지 검증한다.
- Mission을 `CREATED`로 저장한다.
- 선택 Offer를 `ACCEPTED`, 나머지 WAITING Offer를 `REJECTED`, Proposal을 `MATCHED`로 전이한다.

### Persistence Layer

- `offers`는 DB FK 없이 Proposal/User를 참조한다.
- `(proposal_id, runner_id)` unique 제약으로 중복 생성 방어선을 둔다.
- `Mission` unique 제약(`proposal_id`, `offer_id`)과 service 검증으로 중복 수락을 막는다.

## Data/State Impact

- 생성: Offer insert, 필요 시 Proposal `POSTED -> OFFERED`
- 수락: Mission insert, selected Offer `WAITING -> ACCEPTED`, other WAITING Offers `REJECTED`, Proposal `OFFERED -> MATCHED`
- 취소: Offer `WAITING -> CANCELLED`

## Rollout Strategy

1. Offer model/status/repository를 만든다.
2. create/detail/list/own/cancel을 구현한다.
3. Mission model의 최소 생성 경로를 연결한다.
4. accept endpoint를 transaction boundary 안에서 구현한다.
5. Java baseline의 Offer/Mission integration tests와 동일한 FastAPI tests를 작성한다.

## API Behavior Notes

- `OfferResponse`: `id`, `proposalId`, `runnerId`, `runnerName`, `status`, `createdAt`
- `OfferAcceptResponse`: `proposalId`, `offerId`, `missionId`, `proposalStatus`, `acceptedOfferStatus`, `rejectedOfferCount`, `missionStatus`, `ordererId`, `runnerId`, `runFee`, `itemPrice`, `totalAmount`, `createdAt`
