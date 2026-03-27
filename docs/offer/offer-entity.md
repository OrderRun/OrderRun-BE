# Offer Entity

## 필드
- `id`: 식별자 (BigInteger, Primary Key, Auto Increment)
- `proposal_id`: 연결된 Proposal ID (BigInteger, Foreign Key, NOT NULL)
- `runner_id`: 제안을 생성한 러너 사용자 ID (BigInteger, Foreign Key, NOT NULL)
- `estimated_time`: 예상 수행 시간(분) (Integer, NOT NULL)
- `message`: 제안 메시지 (String(500), 선택값)
- `status`: Offer 상태 (Enum, NOT NULL, Default: `WAITING`)
- `created_at`: 생성 일시 (DateTime, NOT NULL, Auto)
- `updated_at`: 수정 일시 (DateTime, NOT NULL, Auto Update)
- `proposal`: 조회 편의용 연관 엔티티, JPA FK 제약 없음 (relationship)
- `runner`: 조회 편의용 연관 엔티티, JPA FK 제약 없음 (relationship)

## Offer Status Enum
- `WAITING`: 대기 중 (기본값)
- `ACCEPTED`: 수락됨
- `REJECTED`: 거절됨

## 규칙

### 생성 규칙
- `proposal_id`, `runner_id`, `estimated_time`는 필수다.
- 생성 시 상태는 항상 `WAITING`이다.
- 같은 `proposal_id + runner_id` 조합으로는 하나의 Offer만 생성 가능하다.
  - UniqueConstraint: `('proposal_id', 'runner_id')`

### 수정 가능 조건
- `WAITING` 상태일 때만 수정 가능하다.

### 상태 전이
- `WAITING` → `ACCEPTED`
- `WAITING` → `REJECTED`

## 검증 제약
- `estimated_time`은 1 이상이어야 한다.
- `message`는 500자를 초과할 수 없다.
- Proposal 상태가 `POSTED` 또는 `OFFERED`일 때만 생성 가능하다.
- SQLAlchemy 연관관계는 foreign_keys 없이 매핑한다.

## DB Schema

```sql
CREATE TABLE offers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    proposal_id BIGINT NOT NULL,
    runner_id BIGINT NOT NULL,
    estimated_time INT NOT NULL,
    message VARCHAR(500),
    status ENUM('WAITING', 'ACCEPTED', 'REJECTED') NOT NULL DEFAULT 'WAITING',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_proposal_runner (proposal_id, runner_id),
    INDEX idx_proposal_id (proposal_id),
    INDEX idx_runner_id (runner_id),
    INDEX idx_status (status)
);
```
