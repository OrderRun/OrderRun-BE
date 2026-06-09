# User API Migration Requirements

## Current Policy

- `User` 도메인은 인증된 현재 사용자 기준의 프로필 조회와 사용자 설정 변경을 담당한다.
- 현재 구현은 `GET /v1/user/detail`, `POST /v1/user/alarm`, `PATCH /v1/user/fcm-token` 을 제공한다.
- 세 API 모두 JWT Bearer 인증이 필요하다.
- 현재 사용자 식별은 `Authorization: Bearer <access_token>` 에서 읽은 `userId` 를 기준으로 한다.
- `GET /v1/user/detail` 은 `id`, `name`, `phone`, `phoneVerifiedAt`, `createdAt`, `lastLoginAt`, `alarmEnabled` 만 반환한다.
- `phone` 은 저장/조회 시 공백과 하이픈을 제거하고, `+82` 로 시작하면 `0` 으로 치환한 정규화 형식을 사용한다.
- `alarmEnabled` 는 사용자 선호값이며 기본값은 `false` 다.
- `fcm-token` 은 사용자당 1개만 유지하는 upsert 정책이다.
- `user` API는 이메일, 닉네임, 평점, 프로필 이미지, 연락처 변경 API를 제공하지 않는다.

## Target Policy

- FastAPI 구현은 현재 Java 구현과 같은 경계, 응답 형식, 상태 코드, 메시지를 그대로 제공한다.
- `user` API는 인증 계층의 현재 사용자 주입에만 의존하고, 전화번호나 FCM 토큰을 통해 사용자를 다시 찾지 않는다.
- 각 API는 성공 시 공통 `ApiResponse` 형식을 유지하고, 실패 시 공통 `ErrorResponse` 형식을 유지한다.

## In Scope

- `GET /v1/user/detail`
- `POST /v1/user/alarm`
- `PATCH /v1/user/fcm-token`
- 현재 사용자 조회용 auth dependency
- `users` / `user_fcm_tokens` 저장 규칙
- 공통 응답/에러 포맷과 인증 실패 처리

## Out Of Scope

- `GET /v1/user/activity`
- 이메일 기반 사용자 프로필
- 전화번호 변경 API
- 평점, 리뷰 수, 프로필 이미지 노출
- 알림 수신/거절 이력 관리

## Acceptance Criteria

### `GET /v1/user/detail`

- 인증된 사용자가 요청하면 200 OK 와 함께 사용자 상세를 반환한다.
- 응답 `data` 는 `id`, `name`, `phone`, `phoneVerifiedAt`, `createdAt`, `lastLoginAt`, `alarmEnabled` 만 포함한다.
- `phone` 은 정규화된 저장값 그대로 반환한다.
- `lastLoginAt` 은 마지막 로그인 시각이며 없을 수 있다.
- 현재 사용자 레코드가 없으면 `USER_NOT_FOUND` 를 반환한다.
- 인증 헤더가 없거나 유효하지 않으면 401 `INVALID_TOKEN` 을 반환한다.

### `POST /v1/user/alarm`

- 요청 본문은 `alarmEnabled` boolean 1개만 허용한다.
- 인증된 사용자의 `alarmEnabled` 값을 업데이트한다.
- 응답은 `data: null` 과 메시지 `알람 설정이 업데이트되었습니다.` 를 반환한다.
- 저장된 값은 즉시 DB 에 반영된다.
- 현재 사용자 레코드가 없으면 `USER_NOT_FOUND` 를 반환한다.
- 인증 실패는 401 `INVALID_TOKEN` 이다.

### `PATCH /v1/user/fcm-token`

- 요청 본문은 `fcmToken` 을 받아야 한다.
- 빈 문자열/공백만 입력은 validation error 로 거부한다.
- 저장 시 앞뒤 공백을 제거한 뒤 upsert 한다.
- 같은 사용자에 대해 여러 번 호출해도 레코드는 1개만 유지된다.
- 응답은 `data: null` 과 메시지 `FCM 토큰이 업데이트되었습니다.` 를 반환한다.
- 현재 사용자 레코드가 없으면 `USER_NOT_FOUND` 를 반환한다.
- 인증 실패는 401 `INVALID_TOKEN` 이다.
