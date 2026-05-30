# Auth API Design

## Decision

- 인증은 phone verification 과 JWT issue/validation 을 분리한다.
- 회원가입과 로그인은 같은 verification 테이블을 공유하되 `purpose` 로 분기한다.
- FastAPI 에서는 `SecurityConfig` 와 동일한 공통 인증 실패 규칙을 유지한다.
- `logout` 은 서버 상태를 바꾸지 않는 no-op 응답으로 유지한다.

## Responsibilities

### API Layer

- 요청 DTO 검증과 공통 응답 래핑을 담당한다.
- `signup`/`login` send 는 public, `refresh` 는 public, `logout` 은 access token 보호로 유지한다.

### Verification Layer

- `auth_phone_verifications` 에 `purpose`, `phone`, `name`, `carrier`, `code_hash`, `status`, `expires_at`, `sent_at`, `verified_at`, `attempt_count` 를 저장한다.
- 최신 유효 `PENDING` 레코드만 재발송 차단 대상으로 본다.
- confirm 시점에는 최신 `PENDING` 레코드를 조회하고, 만료 여부와 코드 일치를 검사한다.
- mismatch 횟수는 레코드 단위로 누적하며 5회 도달 시 `EXPIRED` 로 전환한다.

### User Integration

- `signup confirm` 에서만 신규 `User` 를 생성한다.
- `login confirm` 은 기존 `User` 를 갱신한다.
- `signup confirm` 의 신규 `User` 는 `passwordHash=null`, `alarmEnabled=false`, `phoneVerifiedAt=now`, `lastLoginAt=now` 로 생성한다.

### Token Layer

- access token 은 1시간, refresh token 은 7일을 유지한다.
- subject 는 `userId` 이다.
- token type claim 으로 `access` 와 `refresh` 를 구분한다.
- `refresh` 는 새 access token 만 발급한다.

### SMS Layer

- SMS 발송은 인프라 어댑터로 분리한다.
- 실제 provider 의 예외는 `SMS_SEND_FAILED` 로 변환한다.
- 발송 문자에는 인증 코드와 5분 내 입력 안내가 들어간다.

## Data/State Impact

- `users`
  - signup confirm 에서 insert 된다.
  - `lastLoginAt` 은 signup/login confirm 에서만 갱신된다.
  - `phone` 은 정규화된 문자열로 저장된다.
- `auth_phone_verifications`
  - send 시 insert 된다.
  - confirm 성공/실패/만료에 따라 status 가 바뀐다.
  - 삭제하지 않고 상태 전이로 관리한다.
- `user_fcm_tokens`
  - login confirm 에서 선택적으로 upsert 된다.

## Rollout Strategy

1. 공통 JWT, current-user, error mapping 을 먼저 옮긴다.
2. phone verification storage 와 SMS sender adapter 를 만든다.
3. signup send/confirm 를 먼저 구현한다.
4. login send/confirm 를 그 다음에 구현한다.
5. refresh/logout 을 마지막에 연결한다.
6. 기존 Java 테스트의 assert 를 기준으로 FastAPI integration test 를 맞춘다.

## API Behavior Notes

### `POST /v1/auth/signup/send`

- 입력 검증 후 `PHONE_ALREADY_EXISTS` 와 `PHONE_VERIFICATION_ALREADY_SENT` 를 먼저 검사한다.
- 레코드 저장이 먼저, SMS 전송이 다음이다.
- SMS 전송 실패 시 전체 요청은 실패로 처리한다.

### `POST /v1/auth/signup/confirm`

- 최신 `PENDING` 레코드를 찾고 만료 여부를 먼저 본다.
- 코드 mismatch 는 attempt count 를 증가시키는 별도 커밋 경로를 유지한다.
- 성공 시 verification status 를 `VERIFIED` 로, user 생성과 token 발급을 이어서 수행한다.

### `POST /v1/auth/login/send`

- 사용자 존재 확인 후에만 verification send 를 수행한다.
- 가입되지 않은 번호는 인증 코드 자체를 보내지 않는다.

### `POST /v1/auth/login/confirm`

- verification success 후 user lastLoginAt 을 현재 시각으로 갱신한다.
- `fcmToken` 이 있으면 trim 후 저장한다.

### `POST /v1/auth/refresh`

- token validity 와 `refresh` 타입을 동시에 검사한다.
- 토큰 회전 없이 access token 만 새로 발급한다.

### `POST /v1/auth/logout`

- 서버는 refresh token 상태를 저장하지 않으므로, 요청 성공 여부만 돌려준다.
- access token 보호만 유지하고 내부 상태 변경은 하지 않는다.
