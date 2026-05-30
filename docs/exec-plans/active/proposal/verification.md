# Proposal Migration Verification

## Baseline Tests

- `src/test/java/com/trusty/orderrun/feature/bidding/proposal/ProposalControllerIntegrationTest.java`
- `src/test/java/com/trusty/orderrun/feature/bidding/proposal/ProposalControllerDocsTest.java`
- `src/test/java/com/trusty/orderrun/feature/bidding/proposal/entity/ProposalTest.java`
- `src/test/java/com/trusty/orderrun/feature/bidding/proposal/ProposalRepositoryTest.java`

## Target Behavior Tests

- `GET /v1/proposal`
  - `POSTED`, `OFFERED`만 반환한다.
  - 토큰이 없으면 401이다.
- `GET /v1/proposal/{id}`
  - 존재하는 Proposal 상세를 반환한다.
  - `CANCELLED`도 상세 조회 가능하다.
  - `HOLDING`은 404 `PROPOSAL_NOT_FOUND`다.
  - 없는 ID는 404 `PROPOSAL_NOT_FOUND`다.
- `GET /v1/proposal/own`
  - 현재 사용자의 Proposal만 반환한다.
  - Offer 목록과 `offerCount`를 포함한다.
  - `status` 필터가 동작한다.
- `POST /v1/proposal`
  - 유효 요청은 `HOLDING` 상태로 저장한다.
  - 제목 50자 초과는 400 `VALIDATION_ERROR`다.
  - 내용 500자 초과는 400 `VALIDATION_ERROR`다.
  - 과거 deadline은 400 `PROPOSAL_DEADLINE_INVALID`다.
  - 오프셋 없는 deadline은 400 `INVALID_DATE_TIME_FORMAT`다.
  - 1000원 미만 errandFee는 400 `PROPOSAL_ERRAND_FEE_INVALID`다.
- `PUT /v1/proposal/{id}`
  - `HOLDING`, `POSTED`는 수정 가능하다.
  - `OFFERED`, `MATCHED`, `CANCELLED`는 409 `PROPOSAL_NOT_EDITABLE`이다.
  - 작성자가 아니면 403이다.
- `POST /v1/proposal/{id}/cancel`
  - `HOLDING`, `POSTED`, `OFFERED`는 취소 가능하다.
  - `OFFERED` 취소 시 WAITING Offer는 `REJECTED`다.
  - `MATCHED`, `CANCELLED`는 409 `PROPOSAL_NOT_CANCELLABLE`이다.
  - 작성자가 아니면 403이다.

## Regression Checks

- `ApiResponse`, `PageResponse`, `ErrorResponse` 구조가 유지되는지 확인한다.
- `deadline` 파싱이 오프셋 포함 ISO-8601만 허용하는지 확인한다.
- 생성 직후 상태가 `HOLDING`인지 확인한다.
- 공개 목록과 상세 조회의 `HOLDING` 노출 정책이 유지되는지 확인한다.
- Proposal 취소가 Offer 상태에 미치는 side effect가 유지되는지 확인한다.

## Commands

- `./gradlew test --tests com.trusty.orderrun.feature.bidding.proposal.ProposalControllerIntegrationTest`
- `./gradlew test --tests com.trusty.orderrun.feature.bidding.proposal.ProposalControllerDocsTest`
- `./gradlew test --tests com.trusty.orderrun.feature.bidding.proposal.entity.ProposalTest`
- `./gradlew test --tests com.trusty.orderrun.feature.bidding.proposal.ProposalRepositoryTest`

## Exit Criteria

- Proposal integration/docs/entity/repository tests가 통과한다.
- `docs/api-spec/proposal.md`와 `docs/entity/proposal.md`가 현재 Java 구현과 일치한다.
- FastAPI 구현에서 Java baseline과 동일한 상태 코드, 응답 필드, 에러 코드를 재현할 수 있다.
