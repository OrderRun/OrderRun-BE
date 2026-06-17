# Proposal Model

## 범위

- `proposals`
- `ProposalStatus`

## 1. `proposals`

### 테이블 정보

- 테이블명: `proposals`
- 설명: 행님이 작성한 심부름 모집 공고

### 속성

| 필드명 | 데이터 타입 | Null 허용 | 설명 |
|--------|------------|----------|------|
| `id` | BIGINT | NO | 기본키, auto increment |
| `orderer_id` | VARCHAR(36) | NO | 요청 작성자 User UUID |
| `title` | VARCHAR(50) | NO | 공고 제목 |
| `content` | VARCHAR(500) | NO | 요청 상세 내용 |
| `deadline` | DATETIME(6) | NO | UTC 기준 수행 마감 시각 |
| `errand_fee` | INT | NO | 심부름비 |
| `status` | VARCHAR(20) | NO | Proposal 상태 |
| `meeting_at` | DATETIME(6) | NO | 현재 API/엔티티 미사용. 기존 migration 호환용 |
| `item_price` | INT | NO | 현재 API/엔티티 미사용. 기존 migration 호환용 |
| `deposit` | INT | NO | 현재 API/엔티티 미사용. 기존 migration 호환용 |
| `created_at` | DATETIME(6) | NO | 생성 시각 |
| `updated_at` | DATETIME(6) | NO | 수정 시각 |

### 제약조건

- Primary key: `id`
- Foreign key: 없음
- Indexes:
  - `idx_proposals_orderer_id` on `orderer_id`
- Unique constraints: 없음
- Check constraints: 없음

### 비즈니스 검증 규칙

- `orderer_id`는 존재하는 사용자여야 한다.
- `title`은 공백 불가, 최대 50자다.
- `content`는 공백 불가, 최대 500자다.
- `deadline`은 오프셋 포함 ISO-8601 문자열 입력을 UTC `Instant`로 변환한다.
- `deadline`은 현재 시각보다 미래여야 한다.
- `errand_fee`는 1000원 이상이어야 한다.
- 생성 상태는 `HOLDING`이다.

## 2. `ProposalStatus`

| Status | 의미 |
|--------|------|
| `HOLDING` | 공고 등록 직후, 시스템 계좌 입금 확인 대기 |
| `POSTED` | 관리자 입금 확인 후 게시됨 |
| `OFFERED` | 첫 Offer 생성 이후 |
| `MATCHED` | Offer 수락 이후 |
| `ORDER_COMPLETED` | 오더러 완료 확인 이후 |
| `ALL_COMPLETED` | 러너와 오더러 모두 완료 |
| `DISPUTED` | 분쟁 접수 |
| `RESOLVED` | 분쟁 해결 완료 |
| `CANCELLED` | 매칭 전 취소 |

## 상태 규칙

- `HOLDING -> POSTED`: 관리자 입금 확인 시 DB에서 전환한다.
- `POSTED -> OFFERED`: 첫 Offer 생성 시 전환한다.
- `OFFERED -> MATCHED`: Offer 수락 시 전환한다.
- `MATCHED -> ORDER_COMPLETED`: 오더러 완료 확인 시 전환한다.
- `ORDER_COMPLETED -> ALL_COMPLETED`: 러너 완료도 접수되면 전환한다.
- `HOLDING`, `POSTED`, `OFFERED -> CANCELLED`: 작성자 취소 시 전환한다.
- `HOLDING`, `POSTED` 상태에서만 수정 가능하다.
- 공개 목록은 status 미지정 시 모든 Proposal 상태를 반환하고, 반복 `status` 쿼리로 여러 상태를 필터링한다.
- `HOLDING` 상태는 상세 조회에서 `PROPOSAL_NOT_FOUND`로 숨긴다.
