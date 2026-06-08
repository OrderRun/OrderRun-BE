# Mission Migration Requirements

## Current Policy

- Mission은 Offer 수락 이후 생성되는 실제 수행 계약이다.
- Mission 생성 API는 별도로 없고, 현재 Java 구현에서는 `POST /v1/offer/{offerId}/accept`가 Mission 생성과 Proposal/Offer 상태 전이를 함께 수행한다.
- 모든 Mission 관련 API는 JWT 인증이 필요하다.
- Mission은 생성 시점의 `ordererId`, `runnerId`를 스냅샷으로 저장하며 이후 변경하지 않는다.
- Mission 직접 API는 상태 업데이트만 제공한다. Mission ID 조회는 Proposal/Offer 상세 응답의 `missionId` 필드를 사용한다.
- 러너 전달 완료와 오더 수령 확인은 순서 없이 가능하며 둘 다 기록되면 Mission은 `COMPLETED`, 연결 Offer는 `COMPLETED`가 된다.

## Target Policy

- FastAPI 구현은 현재 Java 구현과 같은 요청/응답/상태 코드/메시지/상태 전이를 유지한다.
- User/Auth, Proposal, Offer에서 만든 current-user dependency와 공통 응답/에러 계약을 그대로 사용한다.
- Payment/Settlement 생성은 현재 Java 구현에서도 연결되지 않았으므로 Mission migration 범위에서는 구현하지 않는다.

## In Scope

- `POST /v1/offer/{offerId}/accept`의 Mission 생성 side effect
- `POST /v1/mission/{missionId}/complete-delivery`
- `POST /v1/mission/{missionId}/confirm-received`
- `POST /v1/mission/{missionId}/dispute`
- `GET /v1/proposal/{proposalId}`의 nullable `missionId`
- `GET /v1/offer/{offerId}`의 nullable `missionId`
- `MissionStatus`
- Mission 생성 actor 스냅샷 필드
- Mission 상태 전이와 actor 권한 검증
- Mission 완료 시 Offer `ACCEPTED -> COMPLETED` 연동

## Out Of Scope

- 별도 Mission 생성 endpoint
- `PATCH /v1/mission/{id}`: 기존 API 문서에는 있으나 현재 Java 컨트롤러에는 없음
- 자동 정산 스케줄러
- Payment 생성과 정산 처리
- 관리자 분쟁 해결 API
- 환불 처리 API

## Acceptance Criteria

### `POST /v1/offer/{offerId}/accept`

- 연결 Proposal 작성자만 호출할 수 있다.
- 요청 본문은 받지 않는다.
- Offer가 없으면 404 `OFFER_NOT_FOUND`다.
- 요청자가 Proposal 작성자가 아니면 403 `FORBIDDEN`이다.
- 이미 Proposal 또는 Offer에 연결된 Mission이 있으면 409 `MISSION_ALREADY_EXISTS`다.
- Offer 상태가 `WAITING`이 아니면 409 `OFFER_NOT_ACCEPTABLE`이다.
- Proposal 상태가 `OFFERED`가 아니면 409 `PROPOSAL_NOT_MATCHABLE`이다.
- 성공 시 Mission은 `CREATED` 상태로 생성된다.
- Mission에는 `proposalId`, `offerId`, `ordererId`, `runnerId`가 저장된다.
- 수락된 Offer는 `ACCEPTED`, 같은 Proposal의 다른 `WAITING` Offer는 `REJECTED`, Proposal은 `MATCHED`가 된다.
- 성공 시 201 Created, 메시지 `제안이 수락되었습니다.`를 반환한다.

### Mission ID 조회

- 별도 `GET /v1/mission` API는 제공하지 않는다.
- Proposal 상세 응답은 연결 Mission이 있으면 `missionId`, 없으면 `null`을 반환한다.
- Offer 상세 응답은 연결 Mission이 있으면 `missionId`, 없으면 `null`을 반환한다.

### Mission 상태 변경

- 존재하지 않는 Mission이면 404 `MISSION_NOT_FOUND`다.
- `action`은 필수이며 `START_PROGRESS`, `COMPLETE_DELIVERY`, `CONFIRM_RECEIVED`, `DISPUTE` 중 하나다.
- `START_PROGRESS`는 runner만 호출할 수 있고 `CREATED -> IN_PROGRESS`로 전이한다.
- `COMPLETE_DELIVERY`는 runner만 호출할 수 있고 `IN_PROGRESS` 또는 `RECEIVED_CONFIRMED`에서만 가능하다.
- `COMPLETE_DELIVERY`에는 `proofImageUrl`이 필수이며 없으면 400 `VALIDATION_ERROR`다.
- `CONFIRM_RECEIVED`는 orderer만 호출할 수 있고 `IN_PROGRESS` 또는 `DELIVERY_COMPLETED`에서만 가능하다.
- `DISPUTE`는 orderer 또는 runner만 호출할 수 있고 `disputeReason`이 필수다.
- 허용되지 않은 actor는 403 `FORBIDDEN`이다.
- 허용되지 않은 상태 전이는 409 `MISSION_NOT_UPDATABLE`이다.
- 러너 전달 완료와 오더 수령 확인이 모두 기록되면 Mission은 `COMPLETED`, 연결 Offer는 `COMPLETED`가 된다.
- 성공 시 200 OK, 메시지 `미션 상태가 업데이트되었습니다.`를 반환한다.
