# Offer Migration Verification

## Baseline Tests

- `src/test/java/com/trusty/orderrun/feature/bidding/offer/OfferControllerIntegrationTest.java`
- `src/test/java/com/trusty/orderrun/feature/bidding/offer/OfferControllerDocsTest.java`
- `src/test/java/com/trusty/orderrun/feature/bidding/offer/entity/OfferTest.java`
- `src/test/java/com/trusty/orderrun/feature/execution/MissionControllerIntegrationTest.java` for Offer accept / Mission creation

## Target Behavior Tests

- `POST /v1/offer`
  - 유효 요청은 WAITING Offer를 만들고 Proposal을 OFFERED로 전이한다.
  - 중복 생성은 409 `DUPLICATE_OFFER`다.
  - 없는 Proposal은 404 `PROPOSAL_NOT_FOUND`다.
  - HOLDING/MATCHED/CANCELLED Proposal은 409 `PROPOSAL_NOT_OPEN`이다.
  - `proposalId` 누락 또는 1 미만은 400 `VALIDATION_ERROR`다.
  - 토큰이 없으면 401이다.
- `POST /v1/offer/{offerId}/accept`
  - WAITING Offer 수락은 Mission 생성, Proposal MATCHED, selected Offer ACCEPTED, other WAITING Offers REJECTED를 만든다.
  - ACCEPTED/REJECTED/CANCELLED Offer는 409 `OFFER_NOT_ACCEPTABLE`이다.
  - POSTED/MATCHED/CANCELLED Proposal은 409 `PROPOSAL_NOT_MATCHABLE`이다.
  - 기존 Mission이 있으면 409 `MISSION_ALREADY_EXISTS`다.
  - 러너 또는 다른 사용자는 403이다.
  - 요청 본문 없이 성공한다.
- `GET /v1/offer/{offerId}`
  - 러너 본인과 Proposal 오더는 조회할 수 있다.
  - 그 외 사용자는 403이다.
  - 없는 Offer는 404 `OFFER_NOT_FOUND`다.
- `GET /v1/offer?proposalId={id}`
  - 생성 시각 내림차순으로 반환한다.
  - Offer가 없으면 빈 배열이다.
  - 없는 Proposal은 404 `PROPOSAL_NOT_FOUND`다.
- `GET /v1/offer/own`
  - 현재 runner 기준으로 페이징 조회한다.
  - `status` 필터가 동작한다.
- `DELETE /v1/offer/{offerId}`
  - WAITING 상태의 본인 Offer는 204와 함께 CANCELLED가 된다.
  - 없는 Offer는 404 `OFFER_NOT_FOUND`다.
  - WAITING이 아니면 409 `OFFER_NOT_CANCELLABLE`이다.
  - 본인이 아니면 403이다.

## Regression Checks

- `ApiResponse`, `PageResponse`, `ErrorResponse` 구조가 유지되는지 확인한다.
- Offer 생성 후 Proposal 상태 전이가 유지되는지 확인한다.
- Offer 수락의 transaction boundary가 유지되는지 확인한다.
- Offer 수락의 Mission 생성과 상태 전이가 한 트랜잭션으로 유지되는지 확인한다.
- `runnerName` 응답 필드가 유지되는지 확인한다.

## Commands

- `./gradlew test --tests com.trusty.orderrun.feature.bidding.offer.OfferControllerIntegrationTest`
- `./gradlew test --tests com.trusty.orderrun.feature.bidding.offer.OfferControllerDocsTest`
- `./gradlew test --tests com.trusty.orderrun.feature.bidding.offer.entity.OfferTest`
- `./gradlew test --tests com.trusty.orderrun.feature.execution.MissionControllerIntegrationTest`

## Exit Criteria

- Offer integration/docs/entity tests와 Offer accept 관련 Mission integration tests가 통과한다.
- `docs/api-spec/README.md`와 `docs/domain.md`의 Offer 계약이 현재 구현 갭과 함께 설명되어 있다.
- FastAPI 구현에서 Java baseline과 동일한 상태 코드, 응답 필드, 에러 코드를 재현할 수 있다.
