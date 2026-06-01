# Mission Model

## 범위

- `missions`
- `MissionStatus`

## 1. `missions`

### 테이블 정보

- 테이블명: `missions`
- 설명: 행님과 꼬봉 간의 실제 수행 계약

### 속성

| 필드명 | 데이터 타입 | Null 허용 | 설명 |
|--------|------------|----------|------|
| `id` | BIGINT | NO | 기본키, auto increment |
| `proposal_id` | BIGINT | NO | 연관 Proposal ID |
| `offer_id` | BIGINT | NO | 수락된 Offer ID |
| `orderer_id` | VARCHAR(36) | NO | 오더 User UUID 스냅샷 |
| `runner_id` | VARCHAR(36) | NO | 러너 User UUID 스냅샷 |
| `delivery_proof_image_url` | VARCHAR(500) | YES | 전달 완료 인증 이미지 URL |
| `status` | VARCHAR(30) | NO | Mission 상태 |
| `pickup_at` | DATETIME(6) | YES | 러너 수행 시작 시각 |
| `delivery_completed_at` | DATETIME(6) | YES | 러너 전달 완료 시각 |
| `received_confirmed_at` | DATETIME(6) | YES | 오더 수령 확인 시각 |
| `settled_at` | DATETIME(6) | YES | 정산 완료 시각 |
| `dispute_reason` | TEXT | YES | 분쟁 접수 사유 |
| `created_at` | DATETIME(6) | NO | 생성 시각 |
| `updated_at` | DATETIME(6) | NO | 수정 시각 |

### 제약조건

- Primary key: `id`
- Foreign key: 없음
- Indexes:
  - `idx_missions_orderer_id` on `orderer_id`
  - `idx_missions_runner_id` on `runner_id`
- Unique constraints:
  - `uk_proposal_id` on `proposal_id`
  - `uk_offer_id` on `offer_id`
- Check constraints: 없음

### 비즈니스 검증 규칙

- Mission은 Offer 수락 시에만 생성한다.
- 생성 조건은 Proposal `OFFERED`, Offer `WAITING`이다.
- 하나의 Proposal에는 최대 하나의 Mission만 생성할 수 있다.
- 하나의 Offer에는 최대 하나의 Mission만 연결할 수 있다.
- 생성 상태는 `CREATED`다.
- `proposal_id`, `offer_id`, `orderer_id`, `runner_id`는 생성 후 수정하지 않는다.

## 2. `MissionStatus`

| Status | 의미 |
|--------|------|
| `CREATED` | Mission 생성 후 러너 수행 시작 전 |
| `IN_PROGRESS` | 러너가 수행을 시작함 |
| `DELIVERY_COMPLETED` | 러너가 전달 완료와 인증 업로드를 마침 |
| `RECEIVED_CONFIRMED` | 오더가 수령 확인을 완료함 |
| `COMPLETED` | 전달 완료와 수령 확인이 모두 끝남 |
| `SETTLED` | 정산 완료 |
| `DISPUTED` | 분쟁 접수 |
| `REFUNDED` | 환불 완료 |

## 상태 규칙

- `CREATED -> IN_PROGRESS`: runner가 `START_PROGRESS`
- `IN_PROGRESS -> DELIVERY_COMPLETED`: runner가 `COMPLETE_DELIVERY`
- `IN_PROGRESS -> RECEIVED_CONFIRMED`: orderer가 `CONFIRM_RECEIVED`
- `DELIVERY_COMPLETED -> COMPLETED`: orderer가 `CONFIRM_RECEIVED`
- `RECEIVED_CONFIRMED -> COMPLETED`: runner가 `COMPLETE_DELIVERY`
- `COMPLETED -> SETTLED`: 시스템 정산. 현재 API 미구현
- `DISPUTED -> REFUNDED`: 시스템 환불. 현재 API 미구현
- `DISPUTED -> SETTLED`: 분쟁 해결 후 정산. 현재 API 미구현
- `DISPUTE`는 orderer 또는 runner만 접수할 수 있다.
- 현재 Java 엔티티는 `SETTLED`, `REFUNDED`에서 `DISPUTE`를 호출해도 예외를 던지지 않고 상태를 변경하지 않는다.
- Mission이 `COMPLETED`로 전이되면 연결 Offer도 `COMPLETED`가 된다.
