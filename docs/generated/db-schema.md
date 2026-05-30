# 생성 DB 스키마 스냅샷

## 목적

현재 아키텍처 문서를 기준으로 정리한 파생 스키마 뷰다.
도메인 모델이나 API 계약이 의미 있게 바뀌면 함께 갱신한다.

## Tables

### `users`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `varchar(36)` | PK |
| `password_hash` | `varchar(255)` | nullable |
| `name` | `varchar(100)` | not null |
| `phone` | `varchar(20)` | unique, nullable |
| `phone_verified_at` | `datetime` | nullable |
| `last_login_at` | `datetime` | nullable |
| `alarm_enabled` | `boolean` | not null |
| `created_at` | `datetime` | not null |
| `updated_at` | `datetime` | not null |

### `auth_phone_verifications`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `bigint` | PK, auto increment |
| `purpose` | `enum` | not null |
| `phone` | `varchar(20)` | not null |
| `name` | `varchar(100)` | nullable |
| `carrier` | `varchar(50)` | nullable |
| `code_hash` | `varchar(100)` | not null |
| `status` | `enum` | not null |
| `expires_at` | `datetime` | not null |
| `sent_at` | `datetime` | not null |
| `verified_at` | `datetime` | nullable |
| `attempt_count` | `int` | not null |
| `created_at` | `datetime` | not null |
| `updated_at` | `datetime` | not null |

### `user_fcm_tokens`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `bigint` | PK, auto increment |
| `user_id` | `varchar(36)` | unique, not null |
| `fcm_token` | `varchar(4096)` | not null |
| `created_at` | `datetime` | not null |
| `updated_at` | `datetime` | not null |

### `terms_agreements`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `bigint` | PK, auto increment |
| `user_id` | `varchar(36)` | unique, not null |
| `terms_of_service` | `boolean` | not null |
| `privacy_policy` | `boolean` | not null |
| `payment_refund_policy` | `boolean` | not null |
| `agreed_at` | `datetime(6)` | not null |
| `created_at` | `datetime(6)` | not null |
| `updated_at` | `datetime(6)` | not null |

### `proposals`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `bigint` | PK, auto increment |
| `orderer_id` | `varchar(36)` | not null, indexed |
| `title` | `varchar(50)` | not null |
| `content` | `varchar(500)` | not null |
| `deadline` | `datetime(6)` | not null |
| `errand_fee` | `int` | not null |
| `status` | `enum(HOLDING, POSTED, OFFERED, MATCHED, CANCELLED)` | not null |
| `meeting_at` | `datetime(6)` | not null, API 미노출 호환 컬럼 |
| `item_price` | `int` | not null, API 미노출 호환 컬럼 |
| `deposit` | `int` | not null, API 미노출 호환 컬럼 |
| `created_at` | `datetime` | not null |
| `updated_at` | `datetime` | not null |

제약:

- DB foreign key 없음
- `idx_proposals_orderer_id` on `orderer_id`

### `offers`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `bigint` | PK, auto increment |
| `proposal_id` | `int` | not null, indexed |
| `runner_id` | `varchar(36)` | not null, indexed |
| `estimated_time` | `int` | not null |
| `message` | `varchar(500)` | nullable |
| `status` | `enum(WAITING, ACCEPTED, REJECTED)` | not null |
| `created_at` | `datetime` | not null |
| `updated_at` | `datetime` | not null |

권장 인덱스:

- `idx_offers_proposal_id`
- `idx_offers_runner_id`
- `uk_offers_proposal_runner`

### `missions`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `bigint` or `uuid` | PK |
| `proposal_id` | FK -> `proposals.id` | not null |
| `accepted_offer_id` | FK -> `offers.id` | unique, not null |
| `customer_id` | FK -> `users.id` (`varchar(36)`) | not null |
| `runner_id` | FK -> `users.id` (`varchar(36)`) | not null |
| `start_at` | `datetime` | nullable |
| `complete_at` | `datetime` | nullable |
| `status` | `enum` | not null |
| `created_at` | `datetime` | not null |
| `updated_at` | `datetime` | not null |

### `payments`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `bigint` or `uuid` | PK |
| `mission_id` | FK -> `missions.id` | unique, not null |
| `payer_id` | FK -> `users.id` (`varchar(36)`) | not null |
| `payee_id` | FK -> `users.id` (`varchar(36)`) | not null |
| `amount` | `decimal(10,2)` | not null |
| `currency` | `varchar(10)` | not null |
| `status` | `enum` | not null |
| `provider` | `varchar(50)` | nullable |
| `external_tx_id` | `varchar(100)` | nullable |
| `created_at` | `datetime` | not null |
| `updated_at` | `datetime` | not null |

## 기준 문서

- `docs/architecture/orderrun-domain-model.md`
- `docs/architecture/orderrun-fastapi-transition.md`
