# User API Verification

## Baseline Tests

- `src/test/java/com/trusty/orderrun/feature/user/UserControllerIntegrationTest.java`
- `src/test/java/com/trusty/orderrun/feature/user/UserControllerDocsTest.java`
- `src/test/java/com/trusty/orderrun/feature/user/UserServiceTest.java`

## Target Behavior Tests

- `GET /v1/user/detail`
  - 유효한 access token 으로 요청하면 `id`, `name`, `phone`, `phoneVerifiedAt`, `createdAt`, `lastLoginAt`, `alarmEnabled` 만 반환한다.
  - `phone` 은 하이픈 제거 및 `+82` 정규화 결과를 반환한다.
  - 인증 없이 호출하면 401 `INVALID_TOKEN` 이다.
  - 존재하지 않는 `userId` 면 404 `USER_NOT_FOUND` 이다.
- `POST /v1/user/alarm`
  - `alarmEnabled=true/false` 가 DB 에 반영된다.
  - 응답 메시지는 `알람 설정이 업데이트되었습니다.` 로 고정된다.
  - 인증 없이 호출하면 401 `INVALID_TOKEN` 이다.
- `PATCH /v1/user/fcm-token`
  - 동일 사용자로 여러 번 호출하면 레코드 1개만 유지된다.
  - 저장된 값은 trim 된 토큰이다.
  - 인증 없이 호출하면 401 `INVALID_TOKEN` 이다.

## Regression Checks

- `ApiResponse` 성공 envelope 가 유지되는지 확인한다.
- `ErrorResponse` 의 `code/message/details/timestamp` 구조가 유지되는지 확인한다.
- 사용자 detail 응답에 email, rating, profile image 같은 불필요한 필드가 추가되지 않는지 확인한다.
- 신규 사용자 기본 `alarmEnabled=false` 가 유지되는지 확인한다.
- `phone` 정규화가 저장과 조회 모두에서 동일하게 동작하는지 확인한다.
- `user_fcm_tokens` 가 사용자당 1개라는 제약이 유지되는지 확인한다.

## Commands

- `./gradlew test --tests com.trusty.orderrun.feature.user.UserControllerIntegrationTest`
- `./gradlew test --tests com.trusty.orderrun.feature.user.UserControllerDocsTest`
- `./gradlew test --tests com.trusty.orderrun.feature.user.UserServiceTest`

## Exit Criteria

- 위 테스트가 모두 통과한다.
- 사용자 API 응답이 현재 Java 구현과 동일한 필드/메시지/상태 코드를 유지한다.
- 인증 실패와 사용자 미존재 예외가 공통 에러 계약으로 반환된다.
