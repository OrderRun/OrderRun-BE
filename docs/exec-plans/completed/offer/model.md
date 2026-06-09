# Offer Model

## 범위

- `offers`
- `OfferStatus`

## 1. `offers`

### 테이블 정보

- 테이블명: `offers`
- 설명: 꼬봉이 Proposal에 제출한 수행 지원서

### 속성

| 필드명 | 데이터 타입 | Null 허용 | 설명 |
|--------|------------|----------|------|
| `id` | BIGINT | NO | 기본키, auto increment |
| `proposal_id` | BIGINT | NO | 대상 Proposal ID |
| `runner_id` | VARCHAR(36) | NO | Offer를 제출한 사용자 ID |
| `status` | VARCHAR(20) | NO | Offer 상태 |
| `created_at` | DATETIME(6) | NO | 생성 시각 |
| `updated_at` | DATETIME(6) | NO | 수정 시각 |

### 제약조건

- Primary key: `id`
- Foreign key: 없음
- Indexes:
  - `idx_offers_runner_id` on `runner_id`
- Unique constraints:
  - `uk_proposal_runner` on (`proposal_id`, `runner_id`)
- Check constraints: 없음

### 비즈니스 검증 규칙

- `proposal_id`는 존재하는 Proposal이어야 한다.
- `runner_id`는 존재하는 사용자여야 한다.
- 동일한 `proposal_id + runner_id` 조합은 하나만 허용한다.
- 생성 상태는 `WAITING`이다.
- Proposal 상태가 `POSTED` 또는 `OFFERED`일 때만 생성 가능하다.

## 2. `OfferStatus`

| Status | 의미 |
|--------|------|
| `WAITING` | 오더의 선택 대기 |
| `ACCEPTED` | 수락되어 Mission 생성에 사용됨 |
| `RUNNER_COMPLETED` | 러너 완료 |
| `ALL_COMPLETED` | 러너와 오더러 모두 완료 |
| `DISPUTED` | 분쟁 접수 |
| `REFUNDED` | 환불 완료 |
| `REJECTED` | 다른 Offer 수락 또는 Proposal 취소로 탈락 |
| `CANCELLED` | 러너가 직접 취소 |

## 상태 규칙

- `WAITING -> ACCEPTED`: Proposal 오더가 Offer 수락
- `WAITING -> REJECTED`: 다른 Offer 수락 또는 Proposal 취소
- `WAITING -> CANCELLED`: 러너 직접 취소
- `ACCEPTED -> RUNNER_COMPLETED`: 러너 완료
- `RUNNER_COMPLETED -> ALL_COMPLETED`: 오더러 완료도 접수됨
- `ACCEPTED/RUNNER_COMPLETED/ALL_COMPLETED -> DISPUTED`: 분쟁 접수
- `DISPUTED -> REFUNDED`: 환불 완료
- 취소는 `WAITING`에서만 가능하다.
- 수락은 `WAITING`에서만 가능하다.
