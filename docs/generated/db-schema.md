# 생성 DB 스키마 스냅샷

## 목적

현재 아키텍처 문서를 기준으로 정리한 파생 스키마 뷰다.
도메인 모델이나 API 계약이 의미 있게 바뀌면 함께 갱신한다.

## Tables

### `users`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `bigint` or `uuid` | PK |
| `email` | `varchar(255)` | unique, not null |
| `nickname` | `varchar(50)` | unique candidate, not null |
| `role` | `enum` | not null |
| `status` | `enum` | not null |
| `phone_number` | `varchar(20)` | nullable |
| `created_at` | `datetime` | not null |
| `updated_at` | `datetime` | not null |

### `proposals`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `bigint` or `uuid` | PK |
| `customer_id` | FK -> `users.id` | not null |
| `title` | `varchar(100)` | not null |
| `description` | `text` | not null |
| `category` | `varchar(50)` | not null |
| `budget_min` | `decimal(10,2)` | nullable |
| `budget_max` | `decimal(10,2)` | nullable |
| `due_at` | `datetime` | nullable |
| `status` | `enum` | not null |
| `created_at` | `datetime` | not null |
| `updated_at` | `datetime` | not null |

### `offers`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `bigint` or `uuid` | PK |
| `proposal_id` | FK -> `proposals.id` | not null |
| `runner_id` | FK -> `users.id` | not null |
| `price` | `decimal(10,2)` | not null |
| `message` | `text` | nullable |
| `eta_minutes` | `int` | nullable |
| `status` | `enum` | not null |
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
| `customer_id` | FK -> `users.id` | not null |
| `runner_id` | FK -> `users.id` | not null |
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
| `payer_id` | FK -> `users.id` | not null |
| `payee_id` | FK -> `users.id` | not null |
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
