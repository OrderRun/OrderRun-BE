# Mission Migration Design

## Decision

- Mission은 Execution context의 aggregate로 구현한다.
- Mission 생성은 Offer 수락 흐름에 포함하고, 별도 Mission 생성 API는 만들지 않는다.
- Mission 상태 업데이트는 current user id와 Mission의 `orderer_id`/`runner_id` 스냅샷 비교로 권한을 검증한다.
- actor id는 생성 시점 스냅샷이며 Mission 상태 업데이트로 변경하지 않는다.
- 정산과 Payment 생성은 후속 settlement migration에서 연결한다.

## Responsibilities

### API Layer

- Mission 상태 변경 endpoint request validation과 ApiResponse wrapping을 담당한다.
- 별도 Mission 조회 endpoint는 제공하지 않고 Proposal/Offer 상세 응답에서 nullable `missionId`를 노출한다.
- `POST /v1/offer/{offerId}/accept`는 Offer API에 속하지만 Mission 생성 결과 필드를 응답에 포함한다.

### Offer Acceptance Service

- Offer 존재 여부와 Proposal 작성자 권한을 검증한다.
- Mission 중복 생성을 차단한다.
- Offer가 `WAITING`, Proposal이 `OFFERED`인지 검증한다.
- Mission을 `CREATED`로 저장한다.
- 선택 Offer를 `ACCEPTED`, 나머지 WAITING Offer를 `REJECTED`, Proposal을 `MATCHED`로 전이한다.

### Mission Service

- Proposal/Offer 상세 조회에서 연결 Mission ID를 조회해 nullable `missionId`로 매핑한다.
- 상태 업데이트 대상 Mission 존재 여부를 검증한다.
- action별 actor 권한과 허용 상태를 검증한다.
- Mission이 새로 `COMPLETED`가 되면 연결 Offer를 `COMPLETED`로 전이한다.

### Persistence Layer

- `missions`는 DB FK 없이 Proposal, Offer, User를 참조한다.
- `proposal_id`, `offer_id`는 각각 unique 제약으로 1:1 연결을 보장한다.
- `orderer_id`, `runner_id`는 생성 후 수정하지 않는다.

## Data/State Impact

- Offer 수락: Mission insert, selected Offer `WAITING -> ACCEPTED`, other WAITING Offers `REJECTED`, Proposal `OFFERED -> MATCHED`
- 수행 시작: Mission `CREATED -> IN_PROGRESS`, `pickup_at` 기록
- 전달 완료: `delivery_proof_image_url`, `delivery_completed_at` 기록 후 필요하면 `COMPLETED`
- 수령 확인: `received_confirmed_at` 기록 후 필요하면 `COMPLETED`
- 완료 연동: Mission `COMPLETED` 전이 시 연결 Offer `ACCEPTED -> COMPLETED`
- 분쟁 접수: Mission `DISPUTED`, `dispute_reason` 기록

## Rollout Strategy

1. Mission model/status/repository를 만든다.
2. Offer 수락 트랜잭션 안에 Mission 생성과 상태 전이를 연결한다.
3. Proposal/Offer 상세 응답에 nullable `missionId`를 연결한다.
4. Mission 상태 업데이트 action을 구현한다.
5. Java baseline integration tests와 동일한 FastAPI tests를 작성한다.

## API Behavior Notes

- `POST /v1/offer/{offerId}/accept`: 요청 본문 없음
- `OfferAcceptResponse`: `proposalId`, `offerId`, `missionId`, `proposalStatus`, `acceptedOfferStatus`, `rejectedOfferCount`, `missionStatus`, `ordererId`, `runnerId`, `createdAt`
- `MissionUpdateRequest`: `action`, `proofImageUrl`, `disputeReason`
- `MissionResponse`: `id`, `proposalId`, `offerId`, `orderer`, `runner`, `deliveryProofImageUrl`, `status`, `pickupAt`, `deliveryCompletedAt`, `receivedConfirmedAt`, `settledAt`, `disputeReason`, `createdAt`
- `MissionResponse.orderer`/`runner`: `id`, `name`, `phone`
