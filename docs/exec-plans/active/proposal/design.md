# Proposal Migration Design

## Decision

- Proposal은 Bidding context의 첫 번째 aggregate root로 구현한다.
- 현재 Java API와 동일하게 `title`, `content`, `deadline`, `errandFee` 중심 모델을 사용한다.
- 날짜 파싱은 API layer에서 수행하고, service layer에는 UTC `Instant`를 전달한다.
- 권한 검사는 current user id와 Proposal `orderer_id` 비교로 수행한다.
- 공개 목록 노출 상태는 `POSTED`, `OFFERED`로 고정한다.

## Responsibilities

### API Layer

- endpoint binding, request validation, deadline parsing을 담당한다.
- `deadline`은 `OffsetDateTime`으로 파싱 가능한 문자열만 허용한다.
- 성공 응답은 `ApiResponse`, 목록 응답은 `PageResponse`로 감싼다.

### Service Layer

- 사용자 존재 여부, Proposal 존재 여부, 작성자 권한, 상태 전이를 검증한다.
- 생성 시 `HOLDING` 상태로 저장한다.
- 수정은 `HOLDING`, `POSTED`에서만 허용한다.
- 취소는 `HOLDING`, `POSTED`, `OFFERED`에서만 허용한다.
- `OFFERED` 취소 시 관련 Offer 중 `WAITING`만 `REJECTED`로 바꾼다.

### Persistence Layer

- `proposals`는 DB FK 없이 `orderer_id`로 User를 참조한다.
- 현재 Java 엔티티는 `meeting_at`, `item_price`, `deposit`을 매핑하지 않는다.
- FastAPI 모델은 현행 API 필드와 상태 규칙을 우선한다.

## Data/State Impact

- 생성: `HOLDING` Proposal insert
- 수정: `title`, `content`, `deadline`, `errand_fee` update
- 취소: Proposal `status=CANCELLED`; `OFFERED`였으면 관련 WAITING Offer `REJECTED`
- 조회: 공개 목록은 `POSTED`, `OFFERED`만 반환

## Rollout Strategy

1. Proposal model/status/repository를 만든다.
2. list/detail/own 조회를 구현한다.
3. create/update/cancel command 흐름을 구현한다.
4. Offer repository 조회를 `own` 응답과 cancel side effect에만 연결한다.
5. Java baseline integration/entity/repository tests와 동일한 FastAPI tests를 작성한다.

## API Behavior Notes

- `ProposalResponse`: `id`, `title`, `content`, `deadline`, `errandFee`, `status`
- `ProposalDetailResponse`: `id`, `title`, `content`, `deadline`, `errandFee`, `status`
- `ProposalOwnResponse`: `id`, `ordererId`, `title`, `content`, `deadline`, `errandFee`, `status`, `offerCount`, `offers`, `createdAt`, `updatedAt`
- `ProposalOwnOfferResponse`: `id`, `proposalId`, `runnerId`, `status`, `createdAt`
