# Auth API Verification

## Baseline Tests

- `src/test/java/com/trusty/orderrun/feature/auth/AuthControllerIntegrationTest.java`
- `src/test/java/com/trusty/orderrun/feature/user/UserControllerIntegrationTest.java` for auth-dependent user access

## Target Behavior Tests

- `POST /v1/auth/signup/send`
  - 정규화된 전화번호로 verification 이 생성되고 SMS 가 1회 호출된다.
  - 기존 전화번호면 409 `PHONE_ALREADY_EXISTS` 이다.
  - 활성 pending 이 있으면 409 `PHONE_VERIFICATION_ALREADY_SENT` 이다.
  - SMS provider 실패는 요청 응답을 실패시키지 않고 verification 을 유지한다.
- `POST /v1/auth/signup/confirm`
  - 성공 시 `users` 가 생성되고 JWT 가 반환된다.
  - 코드 mismatch 는 400 `PHONE_VERIFICATION_CODE_MISMATCH` 이다.
  - 만료된 코드는 400 `PHONE_VERIFICATION_EXPIRED` 이다.
  - 5회 mismatch 후에는 해당 verification 이 `EXPIRED` 로 전환된다.
  - verification 이 없으면 404 `PHONE_VERIFICATION_NOT_FOUND` 이다.
- `POST /v1/auth/login/send`
  - 기존 사용자에게만 SMS 가 발송된다.
  - 미가입 전화번호는 401 `INVALID_CREDENTIALS` 이다.
  - SMS provider 실패는 요청 응답을 실패시키지 않고 verification 을 유지한다.
- `POST /v1/auth/login/confirm`
  - 성공 시 `lastLoginAt` 이 갱신되고, `fcmToken` 이 있으면 저장된다.
  - 코드 mismatch / 만료 / 없음 에 대한 에러 코드가 정확히 반환된다.
- `POST /v1/auth/refresh`
  - 유효한 refresh token 으로 새 access token 을 발급한다.
  - invalid / expired / wrong type token 은 401 `INVALID_TOKEN` 이다.
- `POST /v1/auth/logout`
  - access token 이 있으면 200 OK 와 성공 메시지를 반환한다.
  - 서버 블랙리스트나 토큰 폐기 상태가 생기지 않는다.

## Regression Checks

- `ApiResponse` 성공 envelope 가 유지되는지 확인한다.
- `ErrorResponse` 가 `success=false`, `error`, `timestamp` 구조를 유지하는지 확인한다.
- `phone` 정규화가 send/confirm 전 구간에서 동일한지 확인한다.
- `code_hash` 가 평문이 아닌 해시로 저장되는지 확인한다.
- verification 재발송 차단이 `purpose + phone + active pending` 기준으로 동작하는지 확인한다.
- verification mismatch 후 `attempt_count` 가 증가하는지 확인한다.
- signup confirm 과 login confirm 이 각각 user creation / user update 를 정확히 구분하는지 확인한다.
- refresh token 이 access token 으로 오용되지 않는지 확인한다.

## Commands

- `./gradlew test --tests com.trusty.orderrun.feature.auth.AuthControllerIntegrationTest`
- `./gradlew test --tests com.trusty.orderrun.feature.user.UserControllerIntegrationTest`

## Exit Criteria

- 위 테스트가 모두 통과한다.
- 인증/토큰 응답이 현재 Java 구현과 동일한 필드, 상태 코드, 메시지를 유지한다.
- verification 상태 전이와 실패 횟수 규칙이 동일하게 재현된다.
