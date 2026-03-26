# OrderRun 도메인 모델

## 1. 도메인 구조

`OrderRun` 도메인은 요청 등록, 제안 경쟁, 수행, 정산의 선형 흐름을 가진다.

```text
User
 ├─ creates ──> Proposal
 ├─ submits ──> Offer
 └─ executes ─> Mission

Proposal
 └─ has many ─> Offer

Offer
 └─ accepted into ─> Mission

Mission
 └─ settles via ─> Payment
```

## 2. Aggregate 정의

| Aggregate | 루트 엔티티 | 설명 |
| --- | --- | --- |
| User Aggregate | `User` | 사용자 식별, 프로필, 역할, 약관 동의 |
| Proposal Aggregate | `Proposal` | 요청서 본문, 예산, 상태, 작성자 |
| Offer Aggregate | `Offer` | Proposal에 대한 수행 제안 |
| Mission Aggregate | `Mission` | 수락 이후 실제 수행 단위 |
| Payment Aggregate | `Payment` | 예약, 승인, 취소, 환불, 정산 상태 |

## 3. 엔티티 상세

### 3.1 User

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | bigint / UUID | PK | 사용자 식별자 |
| email | varchar(255) | Unique | 로그인 식별자 |
| nickname | varchar(50) | Unique 후보 | 화면 표시명 |
| role | enum | Required | `customer`, `runner`, `admin` |
| status | enum | Required | `active`, `inactive`, `suspended` |
| phone_number | varchar(20) | Optional | 연락처 |
| created_at | datetime | Required | 생성 시각 |
| updated_at | datetime | Required | 수정 시각 |

비즈니스 규칙:

- 비활성 또는 정지 사용자는 새로운 제안과 수락을 수행할 수 없다.
- 역할은 단일 enum으로 시작하고, 필요 시 역할 매핑 테이블로 확장한다.

### 3.2 Proposal

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | bigint / UUID | PK | 요청서 식별자 |
| customer_id | FK(User) | Required | 요청자 |
| title | varchar(100) | Required | 요청서 제목 |
| description | text | Required | 요청 내용 |
| category | varchar(50) | Required | 심부름/배달/대리구매 등 |
| budget_min | decimal(10,2) | Optional | 희망 최소 금액 |
| budget_max | decimal(10,2) | Optional | 희망 최대 금액 |
| due_at | datetime | Optional | 희망 완료 시각 |
| status | enum | Required | `draft`, `open`, `matched`, `closed`, `cancelled` |
| created_at | datetime | Required | 생성 시각 |
| updated_at | datetime | Required | 수정 시각 |

비즈니스 규칙:

- `open` 상태에서만 Offer를 받을 수 있다.
- 수락된 Offer가 생기면 Proposal은 `matched`로 전이된다.
- Mission이 종료되면 Proposal은 `closed`로 종료된다.

### 3.3 Offer

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | bigint / UUID | PK | 제안 식별자 |
| proposal_id | FK(Proposal) | Required | 대상 요청 |
| runner_id | FK(User) | Required | 제안자 |
| price | decimal(10,2) | Required | 제안 금액 |
| message | text | Optional | 제안 메시지 |
| eta_minutes | int | Optional | 예상 소요 시간 |
| status | enum | Required | `pending`, `accepted`, `rejected`, `withdrawn` |
| created_at | datetime | Required | 생성 시각 |
| updated_at | datetime | Required | 수정 시각 |

비즈니스 규칙:

- 동일 사용자는 하나의 Proposal에 여러 Offer를 남길 수 없도록 제한하는 것을 기본 정책으로 한다.
- 하나의 Proposal에서 `accepted` Offer는 최대 1건이다.

### 3.4 Mission

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | bigint / UUID | PK | 수행 식별자 |
| proposal_id | FK(Proposal) | Required | 원본 요청 |
| accepted_offer_id | FK(Offer) | Required | 채택된 제안 |
| customer_id | FK(User) | Required | 요청자 |
| runner_id | FK(User) | Required | 수행자 |
| start_at | datetime | Optional | 시작 시각 |
| complete_at | datetime | Optional | 완료 시각 |
| status | enum | Required | `ready`, `in_progress`, `completed`, `cancelled`, `disputed` |
| created_at | datetime | Required | 생성 시각 |
| updated_at | datetime | Required | 수정 시각 |

비즈니스 규칙:

- Mission은 Offer 수락 시 생성된다.
- `completed` 이후에는 상태를 되돌리지 않는다. 예외는 운영자 개입을 통한 `disputed` 처리뿐이다.
- Mission 취소 정책은 결제 상태와 함께 검증해야 한다.

### 3.5 Payment

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| id | bigint / UUID | PK | 결제 레코드 |
| mission_id | FK(Mission) | Required | 대상 수행 건 |
| payer_id | FK(User) | Required | 결제자 |
| payee_id | FK(User) | Required | 수익자 |
| amount | decimal(10,2) | Required | 결제 금액 |
| currency | varchar(10) | Required | 기본 `KRW` |
| status | enum | Required | `pending`, `authorized`, `captured`, `refunded`, `failed` |
| provider | varchar(50) | Optional | PG 또는 지급 수단 |
| external_tx_id | varchar(100) | Optional | 외부 거래 ID |
| created_at | datetime | Required | 생성 시각 |
| updated_at | datetime | Required | 수정 시각 |

비즈니스 규칙:

- Mission 생성과 동시에 `pending` 또는 `authorized` 상태를 만들 수 있다.
- Mission 완료 전 `captured`를 허용할지 여부는 정책적으로 결정해야 한다.
- 환불은 `captured` 상태에서만 가능하도록 제한한다.

## 4. 관계 규칙

| 출발 | 도착 | 관계 | 제약 |
| --- | --- | --- | --- |
| User | Proposal | 1:N | 사용자는 여러 요청서를 작성 가능 |
| Proposal | Offer | 1:N | 요청서당 여러 제안 가능 |
| Offer | Mission | 1:0..1 | 수락된 Offer만 Mission 생성 |
| Mission | Payment | 1:1 | MVP는 미션당 결제 1건 기준 |
| User | Mission | 1:N | 요청자/수행자 양쪽 FK 필요 |

## 5. 상태 전이

### 5.1 Proposal 상태

| 현재 상태 | 이벤트 | 다음 상태 | 조건 |
| --- | --- | --- | --- |
| draft | publish | open | 필수값 유효성 통과 |
| open | accept_offer | matched | 유효한 Offer 존재 |
| open | cancel | cancelled | 진행 전 상태 |
| matched | mission_complete | closed | Mission 완료 |
| matched | mission_cancel | cancelled | 정책적으로 허용될 때만 |

### 5.2 Offer 상태

| 현재 상태 | 이벤트 | 다음 상태 | 조건 |
| --- | --- | --- | --- |
| pending | accept | accepted | Proposal이 open |
| pending | reject | rejected | 고객 거절 |
| pending | withdraw | withdrawn | 수행자 철회 |
| accepted | mission_cancel | rejected 또는 유지 | 운영 정책에 따름 |

### 5.3 Mission 상태

| 현재 상태 | 이벤트 | 다음 상태 | 조건 |
| --- | --- | --- | --- |
| ready | start | in_progress | 수행자 시작 |
| in_progress | complete | completed | 완료 확인 |
| ready | cancel | cancelled | 시작 전 취소 |
| in_progress | dispute | disputed | 분쟁 발생 |
| disputed | resolve | completed 또는 cancelled | 운영자 판단 |

### 5.4 Payment 상태

| 현재 상태 | 이벤트 | 다음 상태 | 조건 |
| --- | --- | --- | --- |
| pending | authorize | authorized | 결제 수단 확인 |
| authorized | capture | captured | 미션 완료 또는 정책 충족 |
| authorized | cancel | failed | 승인 취소 |
| captured | refund | refunded | 환불 요청 승인 |
| any | provider_error | failed | 외부 결제 실패 |

## 6. As-Is와 To-Be 비교

| 항목 | As-Is | To-Be |
| --- | --- | --- |
| User | 구현 존재 | 인증, 역할, 약관 동의까지 명확화 |
| Proposal | 구현 존재 | 상태 머신과 예산 정책 정교화 |
| Offer | 구현 존재 | 중복 제안 방지, 수락 규칙 고정 |
| Mission | 구현 존재 | 분쟁, 취소, 완료 확인 절차 강화 |
| Payment | 엔티티 존재, 흐름 미완성 | 예약/확정/환불 상태 모델 완성 |
| Terms | 설계만 존재 | 별도 테이블과 API로 정식화 |
| Notification | 미구현 | 후속 과제로 분리 |
| Admin Dispute | 미구현 | 운영 컨텍스트로 분리 |

## 7. 외부 의존성과 보조 모델

초기 버전에서는 아래 항목을 핵심 Aggregate 밖의 보조 모델로 둔다.

- `TermsAgreement`: 약관 버전별 동의 이력
- `NotificationPreference`: 알림 수신 설정
- `DisputeCase`: 미션 분쟁 관리
- `AuditLog`: 상태 전이 감사 로그

## 8. 데이터 설계 원칙

1. 상태 값은 문자열 enum으로 관리하되 DB에는 명시적 enum 또는 제한된 varchar를 사용한다.
2. 금액은 `decimal(10,2)`를 사용하고 float를 금지한다.
3. 모든 테이블에 `created_at`, `updated_at`을 둔다.
4. 외부 연동 키는 nullable로 두고 도메인 키와 분리한다.
5. 삭제는 hard delete보다 `status` 또는 `deleted_at` 기반 soft delete를 우선 검토한다.

## 9. 구현 우선순위

1. User
2. Proposal
3. Offer
4. Mission
5. Payment
6. TermsAgreement
7. 운영 보조 모델
