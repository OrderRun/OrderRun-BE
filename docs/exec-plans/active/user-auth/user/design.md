# User API Design

## Decision

- `User` 는 얇은 조회/설정 도메인으로 유지한다.
- FastAPI 에서는 `current user` dependency 가 `userId` 를 해석하고, `user` 서비스는 그 식별자만 사용한다.
- `phone` 정규화는 auth/user 모두가 공유하는 순수 함수로 둔다.
- `fcm-token` 은 `users` 테이블에 직접 넣지 않고 `user_fcm_tokens` 테이블로 분리한다.
- `alarmEnabled` 와 `lastLoginAt` 는 사용자 엔티티 상태로 유지한다.

## Responsibilities

### API Layer

- 요청 검증과 응답 직렬화를 담당한다.
- 인증이 필요한 라우트에서 current-user dependency 를 강제한다.
- 성공 응답은 항상 공통 envelope 를 사용한다.

### Service Layer

- `GET /v1/user/detail` 은 사용자 식별자 기준으로 조회 후 DTO 로 변환한다.
- `POST /v1/user/alarm` 은 현재 사용자 레코드를 조회하고 `alarmEnabled` 를 갱신한다.
- `PATCH /v1/user/fcm-token` 은 현재 사용자 기준으로 `user_fcm_tokens` 를 upsert 한다.

### Persistence Layer

- `users`
  - `id` 는 UUID 문자열이다.
  - `phone` 은 unique 이며 정규화된 저장값을 사용한다.
  - `phoneVerifiedAt`, `lastLoginAt`, `alarmEnabled` 는 사용자 상태를 나타낸다.
- `user_fcm_tokens`
  - `user_id` 당 1개만 유지한다.
  - 기존 값이 있으면 갱신하고 없으면 생성한다.

## Data/State Impact

- 사용자 상세 응답은 `users` 의 현재 상태를 그대로 반영한다.
- `alarmEnabled` 는 boolean toggle 이며 별도 이력 테이블을 만들지 않는다.
- `fcmToken` 은 저장 시 trim 하고, 조회/응답에는 노출하지 않는다.
- `phone` 은 저장 직전과 조회 직전 모두 동일한 정규화 규칙을 적용한다.
- 사용자 없음은 비즈니스 예외로 처리한다.

## Rollout Strategy

1. 공통 auth/current-user dependency 를 먼저 구축한다.
2. `User` 모델과 저장소를 옮긴다.
3. `detail`, `alarm`, `fcm-token` API 를 순서대로 구현한다.
4. 현재 Java 응답과 비교하는 integration test 로 계약을 고정한다.

## API Behavior Notes

### `GET /v1/user/detail`

- `UserDetailResponse` 는 엔티티 필드 매핑만 수행한다.
- `phoneVerifiedAt`, `lastLoginAt` 는 null 가능하다.
- `createdAt` 은 공통 BaseEntity 의 감사 시각을 사용한다.

### `POST /v1/user/alarm`

- 요청 값은 `true/false` 둘 중 하나만 허용한다.
- 저장 직후 응답 메시지는 고정 문자열 `알람 설정이 업데이트되었습니다.` 를 사용한다.

### `PATCH /v1/user/fcm-token`

- `fcmToken` 이 유효한 문자열이면 upsert 한다.
- 같은 사용자에 대한 재호출은 기존 레코드를 덮어쓴다.
- 빈 값은 저장하지 않는다.
