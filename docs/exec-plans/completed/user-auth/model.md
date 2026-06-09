# User/Auth Model Docs

`docs/entity/model.md`는 사용자 계정과 인증 보조 모델의 정본 문서다.

## 범위

- `users`
- `auth_phone_verifications`
- `user_fcm_tokens`

## 1. `users`

### 테이블 정보

- 테이블명: `users`
- 설명: 플랫폼을 사용하는 모든 사용자

### 속성

| 필드명 | 데이터 타입 | Null 허용 | 설명 |
|--------|------------|----------|------|
| `id` | VARCHAR(36) | NO | 기본키, UUID |
| `password_hash` | VARCHAR(255) | YES | BCrypt 인코딩 값 |
| `name` | VARCHAR(100) | NO | 사용자 이름 |
| `phone` | VARCHAR(20) | YES | 정규화된 전화번호. 인증 전에는 null 가능 |
| `phone_verified_at` | DATETIME | YES | 전화번호 인증 완료 시각 |
| `last_login_at` | DATETIME | YES | 마지막 로그인 시각 |
| `alarm_enabled` | BOOLEAN | NO | 알람 수신 동의 여부 |
| `created_at` | DATETIME | NO | 가입일 |
| `updated_at` | DATETIME | NO | 수정 시각 |

### 제약조건

- Primary key: `id`
- Foreign key: 없음
- Indexes:
  - `phone` unique
- Unique constraints:
  - `phone`
- Check constraints: DB 레벨 check constraint는 선언하지 않는다.

### 비즈니스 검증 규칙

생성 시:

- `id`는 `@PrePersist`에서 UUID로 생성한다.
- `phone`은 값이 있으면 unique다.
- 초기 `alarm_enabled`는 false다.

기타 규칙:

- `phone` 은 저장 전/후에 동일한 정규화 규칙을 적용한다.
- `updateLastLoginAt(Instant currentTime)`로 UTC 기준 마지막 로그인 시각을 갱신한다.
- `updateAlarmSetting(boolean)`으로 알람 수신 동의를 변경한다.
- `verifyPhone(String phone, Instant verifiedAt)`으로 전화번호 인증 완료 값을 저장한다.

### 관계

- Proposal (as Orderer): 1:N
- Offer (as Runner): 1:N
- Mission (as Orderer): 1:N
- Mission (as Runner): 1:N

### 매핑 메모

- `password_hash` 는 인증 전 사용자 생성에서는 null일 수 있고, 로그인 비밀번호를 사용하지 않는 현재 phone-auth 흐름에서도 유지 필드로 남는다.
- `phone` 은 JPA persist/update 시 하이픈과 공백 제거, `+82` -> `0` 변환 규칙을 적용한다.

## 2. `auth_phone_verifications`

### 테이블 정보

- 테이블명: `auth_phone_verifications`
- 설명: 회원가입/로그인용 전화번호 인증 요청

### 속성

| 필드명 | 데이터 타입 | Null 허용 | 설명 |
|--------|------------|----------|------|
| `id` | BIGINT | NO | 기본키, auto increment |
| `purpose` | VARCHAR(20) | NO | `SIGNUP`, `LOGIN` |
| `phone` | VARCHAR(20) | NO | 정규화된 전화번호 |
| `name` | VARCHAR(100) | YES | 회원가입 요청 시 입력한 이름 |
| `carrier` | VARCHAR(50) | YES | 회원가입 요청 시 입력한 통신사 |
| `code_hash` | VARCHAR(100) | NO | 인증 코드 해시 |
| `status` | VARCHAR(20) | NO | `PENDING`, `VERIFIED`, `EXPIRED` |
| `expires_at` | DATETIME | NO | 만료 시각 |
| `sent_at` | DATETIME | NO | 발송 시각 |
| `verified_at` | DATETIME | YES | 인증 완료 시각 |
| `attempt_count` | INT | NO | 코드 확인 실패 횟수 |
| `created_at` | DATETIME | NO | 생성 시각 |
| `updated_at` | DATETIME | NO | 수정 시각 |

### 제약조건

- Primary key: `id`
- Foreign key: 없음
- Indexes:
  - `(purpose, phone, status, expires_at)`
  - `(purpose, phone, status)`
- Unique constraints: 없음

### 비즈니스 검증 규칙

생성 시:

- 인증 코드는 평문 저장하지 않고 해시만 저장한다.
- 인증 코드 TTL은 5분이다.
- 생성 시 상태는 `PENDING` 이다.
- `attempt_count` 는 0으로 시작한다.

상태 전이:

- `PENDING -> VERIFIED`: 코드 검증 성공
- `PENDING -> EXPIRED`: 만료 확인 또는 실패 횟수 5회 도달

기타 규칙:

- 동일한 `purpose + phone` 조합에서 활성 `PENDING` 이 있으면 재발송하지 않는다.
- 최신 `PENDING` 레코드를 기준으로 confirm 을 수행한다.
- 코드 불일치 시 `attempt_count` 를 1 증가시킨다.
- `attempt_count` 가 5 이상이면 `EXPIRED` 로 바뀐다.

### 관계

- User와 직접 FK 관계는 두지 않는다.

## 3. `user_fcm_tokens`

### 테이블 정보

- 테이블명: `user_fcm_tokens`
- 설명: 사용자별 FCM 등록 토큰 저장소

### 속성

| 필드명 | 데이터 타입 | Null 허용 | 설명 |
|--------|------------|----------|------|
| `id` | BIGINT | NO | 기본키, auto increment |
| `user_id` | VARCHAR(36) | NO | 사용자 ID |
| `fcm_token` | VARCHAR(4096) | NO | FCM 등록 토큰 |
| `created_at` | DATETIME | NO | 생성 시각 |
| `updated_at` | DATETIME | NO | 수정 시각 |

### 제약조건

- Primary key: `id`
- Foreign key: 없음
- Unique constraints:
  - `user_id`
- Check constraints: 없음

### 비즈니스 검증 규칙

- 사용자당 1개만 유지한다.
- 동일 사용자에 대해 재호출되면 upsert 한다.
- 저장 전 `trim()` 을 적용한다.
- 빈 문자열은 저장하지 않는다.

### 관계

- User: 1:1

### 매핑 메모

- 토큰 값은 응답에 노출하지 않는다.
- 기존 레코드가 있으면 토큰만 갱신한다.
