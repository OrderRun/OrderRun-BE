# Mission Migration Verification

## Baseline Tests

- `src/test/java/com/trusty/orderrun/feature/execution/MissionControllerIntegrationTest.java`

## Target Behavior Tests

- `POST /v1/offer/{offerId}/accept`
  - WAITING Offer를 수락하면 Mission을 `CREATED`로 생성한다.
  - 수락된 Offer는 `ACCEPTED`, 다른 WAITING Offer는 `REJECTED`, Proposal은 `MATCHED`가 된다.
  - `ACCEPTED`, `REJECTED`, `CANCELLED` Offer는 409 `OFFER_NOT_ACCEPTABLE`이다.
  - `POSTED`, `MATCHED`, `CANCELLED` Proposal은 409 `PROPOSAL_NOT_MATCHABLE`이다.
  - 존재하지 않는 Offer는 404 `OFFER_NOT_FOUND`다.
  - 이미 Mission이 있으면 409 `MISSION_ALREADY_EXISTS`다.
  - 토큰이 없으면 401이다.
  - Proposal 작성자가 아니면 403 `FORBIDDEN`이다.
  - 요청 본문 없이 성공한다.
- `GET /v1/mission`
  - `role` 기본값은 `ORDERER`다.
  - `role=ORDERER`는 현재 사용자가 orderer인 Mission만 반환한다.
  - `role=RUNNER`는 현재 사용자가 runner인 Mission만 반환한다.
  - `status` 필터가 동작한다.
  - 응답은 PageResponse다.
- `PUT /v1/mission/{id}`
  - runner가 `START_PROGRESS`를 호출하면 `CREATED -> IN_PROGRESS`다.
  - runner 전달 완료 후 orderer 수령 확인을 하면 Mission과 Offer가 완료된다.
  - orderer 수령 확인 후 runner 전달 완료를 해도 Mission과 Offer가 완료된다.
  - `COMPLETE_DELIVERY`에 `proofImageUrl`이 없으면 400 `VALIDATION_ERROR`다.
  - 완료된 Mission에 완료 액션을 다시 요청하면 409 `MISSION_NOT_UPDATABLE`이다.
  - action별 권한이 아닌 사용자는 403 `FORBIDDEN`이다.

## Regression Checks

- `ApiResponse`, `PageResponse`, `ErrorResponse` 구조가 유지되는지 확인한다.
- Offer 수락과 Mission 생성이 단일 트랜잭션으로 처리되는지 확인한다.
- Mission 생성 실패 시 Offer/Proposal 상태가 변경되지 않는지 확인한다.
- Mission 완료 전에는 Offer가 `ACCEPTED`로 유지되는지 확인한다.
- Mission 완료 시에만 Offer가 `COMPLETED`로 전이되는지 확인한다.
- Mission actor 스냅샷 필드가 상태 업데이트로 변경되지 않는지 확인한다.
- 현재 구현에 없는 `PATCH /v1/mission/{id}`를 FastAPI에 추가하지 않았는지 확인한다.

## Commands

- `./gradlew test --tests com.trusty.orderrun.feature.execution.MissionControllerIntegrationTest`

## Exit Criteria

- Mission integration tests가 통과한다.
- `docs/api-spec/README.md`, `docs/domain.md`와 현재 구현 차이를 구현 범위/범위 밖 메모로 설명할 수 있다.
- FastAPI 구현에서 Java baseline과 동일한 상태 코드, 응답 필드, 에러 코드를 재현할 수 있다.
