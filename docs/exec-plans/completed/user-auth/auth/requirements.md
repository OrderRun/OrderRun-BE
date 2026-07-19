# Auth API Migration Requirements

## Current Policy

- 현재 구현은 전화번호 기반 회원가입/로그인과 토큰 갱신/로그아웃을 제공한다.
- 인증 코드는 `auth_phone_verifications` 에 저장되고, 평문이 아니라 해시로만 보관된다.
- 인증 코드는 5분 동안 유효하다.
- 같은 `purpose + phone` 조합에 대해 유효한 `PENDING` 인증이 있으면 재발송할 수 없다.
- 인증 실패 횟수는 최대 5회까지 허용된다.
- 회원가입 성공 시 `User` 가 생성되고 JWT access/refresh 토큰이 함께 발급된다.
- 로그인 성공 시 기존 `User` 의 `lastLoginAt` 을 갱신하고 JWT 가 발급된다.
- 로그인 성공 시 선택적으로 `fcmToken` 을 함께 저장한다.
- `refresh` 는 새 access token 만 발급한다. refresh token rotation 은 하지 않는다.
- `logout` 은 서버 블랙리스트를 두지 않으며, 클라이언트 토큰 삭제를 전제로 한다.

## Target Policy

- FastAPI 구현은 현재 Java 구현과 같은 요청/응답/에러 코드/상태 전이를 그대로 제공한다.
- 회원가입과 로그인은 SMS 인증 절차를 반드시 통과해야 한다.
- phone normalization, code TTL, attempt count, token type 검증, user creation 시점은 현재 구현과 동일해야 한다.
- 단, `development`/`local`/`staging` 환경의 `POST /v1/auth/login/confirm` 은 기존 사용자에 한해 테스트 코드 `123456` 을 SMS pending 없이 허용한다.

## In Scope

- `POST /v1/auth/signup/send`
- `POST /v1/auth/signup/confirm`
- `POST /v1/auth/login/send`
- `POST /v1/auth/login/confirm`
- `POST /v1/auth/refresh`
- `POST /v1/auth/logout`
- `auth_phone_verifications` 상태/TTL/attempt 규칙
- JWT issue/validate/refresh 규칙
- SMS sender abstraction

## Out Of Scope

- 서버 측 refresh blacklist
- 이메일/소셜 로그인
- 비밀번호 로그인
- 전화번호 변경 인증 API
- push 알림 발송 로직

## Acceptance Criteria

### `POST /v1/auth/signup/send`

- 요청은 `name`, `phone`, `carrier` 를 받는다.
- `name` 과 `carrier` 는 trim 해서 저장한다.
- `phone` 은 공백/하이픈 제거 후 `+82` 를 `0` 으로 바꾸는 정규화 규칙을 적용한다.
- 이미 사용 중인 전화번호가 있으면 409 `PHONE_ALREADY_EXISTS` 를 반환한다.
- 동일한 `purpose=SIGNUP` 의 활성 `PENDING` 인증이 있으면 409 `PHONE_VERIFICATION_ALREADY_SENT` 를 반환한다.
- 성공 시 인증 코드 레코드를 생성하고 SMS 발송을 백그라운드 작업으로 예약한다.
- 성공 응답 `data` 는 `phone`, `expiresAt` 을 가진다.
- `phone` 은 정규화된 전화번호다.
- `expiresAt` 은 현재 시각 + 5분이다.
- SMS provider 오류는 요청 응답을 실패시키지 않으며 서버 로그로 남긴다.

### `POST /v1/auth/signup/confirm`

- 요청은 `phone`, `code`, `fcmToken?` 를 받는다.
- 최신 `PENDING` 회원가입 인증을 찾는다.
- 인증이 없으면 404 `PHONE_VERIFICATION_NOT_FOUND` 를 반환한다.
- 만료되었으면 400 `PHONE_VERIFICATION_EXPIRED` 를 반환하고 해당 인증을 `EXPIRED` 로 바꾼다.
- 코드가 틀리면 400 `PHONE_VERIFICATION_CODE_MISMATCH` 를 반환하고 실패 횟수를 1 증가시킨다.
- 실패 횟수가 5회에 도달하면 해당 인증은 `EXPIRED` 로 바뀐다.
- 성공 시 인증은 `VERIFIED` 로 바뀌고 `User` 가 생성된다.
- 생성된 사용자의 `phoneVerifiedAt` 과 `lastLoginAt` 은 현재 시각으로 설정된다.
- `fcmToken` 이 있으면 trim 후 저장한다.
- 생성 직후 JWT access/refresh token 이 함께 발급된다.
- 성공 응답 `data` 는 `accessToken`, `refreshToken`, `tokenType`, `expiresIn`, `userId` 를 가진다.
- `tokenType` 은 항상 `Bearer` 다.
- `expiresIn` 은 access token 만료 시간(밀리초)이다.
- 이미 같은 전화번호를 가진 사용자가 생겼으면 409 `PHONE_ALREADY_EXISTS` 를 반환한다.

### `POST /v1/auth/login/send`

- 요청은 `phone` 만 받는다.
- 정규화된 전화번호로 기존 사용자를 찾아야 한다.
- 사용자가 없으면 401 `INVALID_CREDENTIALS` 를 반환한다.
- 동일한 `purpose=LOGIN` 의 활성 `PENDING` 인증이 있으면 409 `PHONE_VERIFICATION_ALREADY_SENT` 를 반환한다.
- 성공 시 인증 코드 레코드를 생성하고 SMS 발송을 백그라운드 작업으로 예약한다.
- 성공 응답 `data` 는 `phone`, `expiresAt` 을 가진다.
- `phone` 은 정규화된 전화번호다.
- SMS provider 오류는 요청 응답을 실패시키지 않으며 서버 로그로 남긴다.

### `POST /v1/auth/login/confirm`

- 요청은 `phone`, `code`, `fcmToken?` 를 받는다.
- `development`/`local`/`staging` 에서 `code=123456` 이고 기존 사용자가 있으면 로그인 인증 레코드 없이도 성공한다.
- 위 테스트 코드 우회는 로그인 확인 API 전용이며 `production` 과 회원가입 확인에는 적용되지 않는다.
- 최신 `PENDING` 로그인 인증을 찾는다.
- 인증이 없으면 404 `PHONE_VERIFICATION_NOT_FOUND` 를 반환한다.
- 만료되었으면 400 `PHONE_VERIFICATION_EXPIRED` 를 반환하고 해당 인증을 `EXPIRED` 로 바꾼다.
- 코드가 틀리면 400 `PHONE_VERIFICATION_CODE_MISMATCH` 를 반환하고 실패 횟수를 증가시킨다.
- 성공 시 인증은 `VERIFIED` 로 바뀌고 기존 사용자의 `lastLoginAt` 이 갱신된다.
- `fcmToken` 이 있으면 trim 후 저장한다.
- 성공 시 JWT access/refresh token 이 함께 발급된다.
- 성공 응답 `data` 는 `accessToken`, `refreshToken`, `tokenType`, `expiresIn`, `userId` 를 가진다.
- `tokenType` 은 항상 `Bearer` 다.
- 가입되지 않은 전화번호는 확인 단계에서 404 `USER_NOT_FOUND` 로 거부된다.
- 가입되지 않은 전화번호는 인증 발송 단계에서 401 `INVALID_CREDENTIALS` 로 거부된다.

### `POST /v1/auth/refresh`

- 요청은 `refreshToken` 을 받는다.
- 토큰이 없거나, 서명이 틀리거나, 만료되었거나, refresh 타입이 아니면 401 `INVALID_TOKEN` 을 반환한다.
- 토큰의 subject 에 해당하는 사용자가 없으면 404 `USER_NOT_FOUND` 를 반환한다.
- 성공 응답 `data` 는 `accessToken`, `expiresIn` 을 가진다.
- refresh token 은 재발급하지 않는다.

### `POST /v1/auth/logout`

- 요청은 `refreshToken` 을 받지만 서버는 이를 블랙리스트에 저장하지 않는다.
- 현재 구현은 access token 인증이 필요한 보호 엔드포인트다.
- 성공 응답은 `data: null` 이다.
- 성공 시 항상 `로그아웃 되었습니다.` 메시지를 반환한다.
- 서버 상태 변화는 없다.

## Auth State Rules

- `PENDING -> VERIFIED` 는 성공 confirm 에서만 발생한다.
- `PENDING -> EXPIRED` 는 만료 확인 또는 5회 실패 도달 시 발생한다.
- `VERIFIED` 와 `EXPIRED` 는 재검증 대상이 아니다.
- `active pending` 은 `status=PENDING` 이면서 `expiresAt > now` 인 레코드만 의미한다.
- 만료된 `PENDING` 은 재발송을 막지 않는다.
