# Offer Entity

## 필드
- `id`: 식별자 (BigInteger, Primary Key, Auto Increment)
- `proposal_id`: 연결된 Proposal ID (BigInteger, NOT NULL, DB FK 없음)
- `runner_id`: 제안을 생성한 러너 User UUID (VARCHAR(36), NOT NULL, DB FK 없음)
- `status`: Offer 상태 (Enum, NOT NULL, Default: `WAITING`)
- `created_at`: 생성 일시 (DateTime, NOT NULL, Auto)
- `updated_at`: 수정 일시 (DateTime, NOT NULL, Auto Update)

## Offer Status Enum
- `WAITING`: 대기 중 (기본값)
- `ACCEPTED`: 수락됨
- `COMPLETED`: 러너 완료
- `ALL_COMPLETED`: 러너와 오더러 모두 완료
- `SETTLED`: 정산 완료
- `DISPUTED`: 분쟁 접수
- `REFUNDED`: 환불 완료
- `REJECTED`: 거절됨
- `CANCELLED`: 러너 직접 취소

## 규칙

### 생성 규칙
- `proposal_id`는 요청 body의 필수값이다.
- `runner_id`는 인증 사용자 ID에서 결정한다.
- 생성 시 상태는 항상 `WAITING`이다.
- 같은 `proposal_id + runner_id` 조합으로는 하나의 Offer만 생성 가능하다.
  - UniqueConstraint: `uk_proposal_runner` on (`proposal_id`, `runner_id`)

### 취소 가능 조건
- `WAITING` 상태일 때만 러너 본인이 취소 가능하다.

### 상태 전이
- `WAITING` -> `ACCEPTED`
- `WAITING` -> `REJECTED`
- `WAITING` -> `CANCELLED`
- `ACCEPTED` -> `COMPLETED`
- `COMPLETED` -> `ALL_COMPLETED`
- `ALL_COMPLETED` -> `SETTLED`
- `ACCEPTED`/`COMPLETED`/`ALL_COMPLETED` -> `DISPUTED`
- `DISPUTED` -> `REFUNDED`

## 검증 제약
- Proposal 상태가 `POSTED` 또는 `OFFERED`일 때만 생성 가능하다.
- SQLAlchemy 모델은 DB foreign key 없이 ID 값으로 참조한다.

## DB Schema

```sql
CREATE TABLE offers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    proposal_id BIGINT NOT NULL,
    runner_id VARCHAR(36) NOT NULL,
    status ENUM('WAITING', 'ACCEPTED', 'COMPLETED', 'ALL_COMPLETED', 'SETTLED', 'DISPUTED', 'REFUNDED', 'REJECTED', 'CANCELLED') NOT NULL DEFAULT 'WAITING',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_proposal_runner (proposal_id, runner_id),
    INDEX idx_proposal_id (proposal_id),
    INDEX idx_runner_id (runner_id),
    INDEX idx_status (status)
);
```
