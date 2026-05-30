# Terms Agreement Design

## Decision

- Terms는 User/Auth 이후에 구현하는 독립 부가 도메인으로 둔다.
- API는 `POST /v1/terms` 하나만 제공한다.
- 약관 항목은 `TermsType` enum으로 관리한다.
- 저장은 사용자별 최신 동의 상태 1건만 유지하는 upsert 정책으로 한다.
- 약관 버전과 이력은 현재 범위에서 제외한다.

## Responsibilities

### API Layer

- `POST /v1/terms` 요청을 받고 current-user dependency에서 `userId`를 얻는다.
- 요청 본문 validation을 수행한다.
- 성공 시 201 Created와 공통 `ApiResponse`를 반환한다.

### Service Layer

- `userId`가 실제 사용자에 해당하는지 확인한다.
- `TermsType.required=true`인 항목이 모두 동의되었는지 검증한다.
- 현재 시각을 `agreedAt`으로 잡는다.
- 기존 동의 row가 있으면 갱신하고, 없으면 생성한다.

### Persistence Layer

- `terms_agreements.user_id`는 unique다.
- DB FK는 만들지 않고 애플리케이션 레벨에서 사용자 존재를 검증한다.
- `created_at`, `updated_at`은 공통 감사 필드로 관리한다.

## Data/State Impact

- 최초 동의는 `terms_agreements` insert다.
- 재동의는 같은 row update다.
- 재동의 시 세 boolean 필드와 `agreed_at`이 모두 새 요청 값/시각으로 교체된다.
- 응답에는 저장된 최신 row 상태만 포함한다.

## Rollout Strategy

1. User/Auth의 인증 기반을 먼저 사용 가능하게 한다.
2. `TermsAgreement` 모델과 repository를 만든다.
3. `TermsType` enum과 request/response schema를 만든다.
4. `POST /v1/terms` 서비스를 구현한다.
5. Java baseline 테스트와 동일한 FastAPI integration test를 작성한다.

## API Behavior Notes

### `POST /v1/terms`

- endpoint: `/v1/terms`
- method: `POST`
- auth: required
- success status: `201 Created`
- success message: `약관 동의가 완료되었습니다.`
- request fields:
  - `termsOfService`: required boolean, must be `true`
  - `privacyPolicy`: required boolean, must be `true`
  - `paymentRefundPolicy`: required boolean, must be `true`
- response fields:
  - `userId`
  - `termsOfService`
  - `privacyPolicy`
  - `paymentRefundPolicy`
  - `agreedAt`
