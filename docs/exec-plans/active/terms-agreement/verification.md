# Terms Agreement Verification

## Baseline Tests

- `src/test/java/com/trusty/orderrun/feature/terms/TermsControllerIntegrationTest.java`
- `src/test/java/com/trusty/orderrun/feature/terms/TermsControllerDocsTest.java`

## Target Behavior Tests

- `POST /v1/terms`
  - 세 필드가 모두 `true`이면 201 Created와 저장된 동의 정보를 반환한다.
  - 응답 메시지는 `약관 동의가 완료되었습니다.`다.
  - 응답 `data.userId`는 토큰의 현재 사용자 ID다.
  - 같은 사용자가 다시 호출하면 row가 1건만 유지된다.
  - 재호출 시 `agreedAt`이 갱신된다.
  - 필수 필드 누락은 400 `VALIDATION_ERROR`다.
  - 필수 필드 `null`은 400 `VALIDATION_ERROR`다.
  - 필수 필드 `false`는 400 `VALIDATION_ERROR`다.
  - 토큰이 없으면 401 `INVALID_TOKEN`이다.
  - 토큰의 사용자 ID가 존재하지 않으면 `USER_NOT_FOUND`다.

## Regression Checks

- User/Auth current-user dependency가 그대로 동작하는지 확인한다.
- 공통 `ApiResponse`와 `ErrorResponse` 구조가 유지되는지 확인한다.
- `terms_agreements.user_id` unique 제약이 유지되는지 확인한다.
- DB FK 없이도 서비스 레이어에서 사용자 존재 검증을 수행하는지 확인한다.
- 약관 필드가 `TermsType` 필수 항목과 일치하는지 확인한다.

## Commands

- `./gradlew test --tests "*Terms*"`
- `./gradlew test --tests com.trusty.orderrun.feature.terms.TermsControllerIntegrationTest`
- `./gradlew test --tests com.trusty.orderrun.feature.terms.TermsControllerDocsTest`

## Exit Criteria

- 약관 통합 테스트와 문서 테스트가 통과한다.
- `docs/api-spec/terms.md`와 `docs/entity/terms-agreement.md`가 구현과 일치한다.
- FastAPI 마이그레이션 시에도 Java baseline과 동일한 상태 코드, 응답 필드, 에러 코드를 재현할 수 있다.
