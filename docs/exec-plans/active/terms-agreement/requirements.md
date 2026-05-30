# Terms Agreement Requirements

## Current Policy

- 로그인된 사용자가 필수 약관 3개에 동의한 사실을 저장한다.
- 현재 API는 `POST /v1/terms` 하나만 제공한다.
- 약관 항목은 `TermsType` enum으로 이름과 필수 여부를 관리한다.
- 현재 필수 약관은 이용약관, 개인정보처리방침, 결제/환불지급정책 3개다.
- 사용자별 약관 동의 row는 1건만 유지한다.
- 같은 사용자의 재호출은 기존 row를 갱신한다.

## Target Policy

- FastAPI 구현은 현재 Java 구현과 같은 요청/응답/상태 코드/메시지를 유지한다.
- User/Auth에서 만든 current-user dependency와 공통 응답/에러 계약을 그대로 사용한다.
- 약관 동의는 사용자 생성 이후 호출되는 사용자 부가 정책으로 취급한다.

## In Scope

- `POST /v1/terms`
- `terms_agreements` 모델
- `TermsType` enum
- 사용자 존재 검증
- 사용자별 upsert
- 필수 약관 validation

## Out Of Scope

- 약관 버전 관리
- 과거 동의 이력 보관
- 선택 약관 관리
- 약관 본문 조회 API
- 약관 철회 API

## Acceptance Criteria

### `POST /v1/terms`

- 인증된 사용자만 호출할 수 있다.
- 요청 필드는 `termsOfService`, `privacyPolicy`, `paymentRefundPolicy`다.
- 세 필드는 모두 필수이며 `true`여야 한다.
- 필드 누락, `null`, `false`는 400 `VALIDATION_ERROR`다.
- 인증 토큰이 없거나 유효하지 않으면 401 `INVALID_TOKEN`이다.
- 토큰의 사용자 ID가 존재하지 않으면 `USER_NOT_FOUND`를 반환한다.
- 성공 시 201 Created를 반환한다.
- 성공 응답 `data`는 `userId`, `termsOfService`, `privacyPolicy`, `paymentRefundPolicy`, `agreedAt`을 가진다.
- 성공 메시지는 `약관 동의가 완료되었습니다.`다.
- 최초 호출은 `terms_agreements` row를 생성한다.
- 재호출은 같은 `user_id`의 기존 row를 갱신하고 row 수를 1건으로 유지한다.
- 재호출 시 `agreed_at`은 새 요청 처리 시각으로 갱신된다.
