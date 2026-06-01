# Persistence Schema Canonicalization

## 문제 정의

현재 저장소의 영속성 기준은 세 출처에 흩어져 있다.

- 실제 SQLAlchemy 모델: `app/models/`
- 기존 문서 스냅샷: `docs/generated/db-schema.md`, `docs/exec-plans/active/*/model.md`
- 목표 전체 스키마: 사용자 제공 테이블 정의

세 출처가 일부 다르기 때문에 결제/정산, Mission 컬럼, FK 정책, legacy 인증 테이블의 기준을 먼저 고정해야 한다.

## 배경과 제약

- 현재 기술 스택은 FastAPI, SQLAlchemy 2.x, MySQL 8.x다.
- 사용자 제공 스키마는 JPA 매핑 여부를 포함하지만, 이 저장소에서는 ORM 매핑 여부로 해석한다.
- 하네스 규칙상 영속성 모델과 마이그레이션 방향은 설계 문서에 남긴 뒤 파생 문서를 갱신한다.
- 실제 MySQL FK constraint는 목표 정본에서 두지 않는다. 관계는 애플리케이션 레벨에서 검증한다.

## 결정 내용

사용자 제공 전체 스키마를 목표 정본으로 채택한다.

정본 테이블은 다음 10개다.

| 테이블 | 담당 도메인 | 목표 ORM 매핑 | 설명 |
|--------|-------------|---------------|------|
| `users` | user/auth | O | 사용자 계정 |
| `auth_phone_verifications` | auth | O | 회원가입/로그인 전화번호 인증 |
| `phone_verifications` | user legacy | X | 구 전화번호 인증 테이블 |
| `user_fcm_tokens` | user | O | 사용자별 FCM 토큰 |
| `terms_agreements` | terms | O | 사용자별 필수 약관 동의 |
| `proposals` | bidding/proposal | O | 심부름 모집 공고 |
| `offers` | bidding/offer | O | 러너 지원서 |
| `missions` | execution | O | 매칭 후 수행 계약 |
| `payments` | settlement | O | 결제/정산 처리 |
| `settlement_accounts` | settlement | O | 러너 정산 계좌 |

목표 관계는 아래처럼 문서화한다.

```text
users 1 -> N proposals(orderer_id)
users 1 -> N offers(runner_id)
users 1 -> N missions(orderer_id, runner_id)
users 1 -> 1 user_fcm_tokens
users 1 -> 1 terms_agreements
users 1 -> 1 settlement_accounts

proposals 1 -> N offers
proposals 1 -> 1 missions
offers 1 -> 1 missions
missions 1 -> 1 payments
```

공통 감사 컬럼은 모든 현재 JPA/ORM 대상 테이블에 `created_at`, `updated_at`을 `datetime(6) NOT NULL` 기준으로 둔다. 스테이징 DB 기준으로 DB default는 두지 않고, SQLAlchemy ORM의 `default`/`onupdate`에서 UTC timestamp를 채운다. Legacy `phone_verifications`도 migration 기준으로 감사 컬럼을 가진 것으로 기록한다.

## 현재 확인 결과

현재 코드에서 확인한 SQLAlchemy 모델 기준 상태는 다음과 같다.

| 테이블 | 현재 코드 상태 | 목표 정본과의 상태 |
|--------|----------------|--------------------|
| `users` | `app/models/user.py`에 있음 | 대체로 일치 |
| `auth_phone_verifications` | `app/models/user.py`에 있음 | 대체로 일치. 인덱스명은 현재 `expires_at` suffix 포함 |
| `phone_verifications` | 모델 없음 | 목표상 legacy 테이블로만 문서화 |
| `user_fcm_tokens` | `app/models/user.py`에 있음 | 대체로 일치 |
| `terms_agreements` | `app/models/terms.py`에 있음 | 대체로 일치 |
| `proposals` | `app/models/proposal.py`에 있음 | 대체로 일치. `meeting_at`, `item_price`, `deposit`은 호환 컬럼으로 매핑됨 |
| `offers` | `app/models/offer.py`에 있음 | 대체로 일치 |
| `missions` | `app/models/mission.py`에 있음 | 컬럼명, 금액 타입, FK 정책 차이 있음 |
| `payments` | 모델 없음 | 목표 정본 기준 미구현 |
| `settlement_accounts` | 모델 없음 | 목표 정본 기준 미구현 |

현재 코드에는 목표 정본 외 보조 테이블도 있다.

| 테이블 | 모델 | 처리 방향 |
|--------|------|-----------|
| `device_tokens` | `app/models/notification.py` | 알림 시스템 보조 테이블로 별도 문서화 |
| `notifications` | `app/models/notification.py` | 알림 시스템 보조 테이블로 별도 문서화 |
| `notification_preferences` | `app/models/notification.py` | 알림 시스템 보조 테이블로 별도 문서화 |

## 주요 갭

### Mission

목표 정본은 다음 기준을 사용한다.

- 실제 MySQL FK constraint 없음
- `proposal_id`, `offer_id`, `orderer_id`, `runner_id`는 애플리케이션 레벨 관계
- 진행 시각 컬럼은 `pickup_at`, `delivery_completed_at`, `received_confirmed_at`, `settled_at`
- `proposal_id`, `offer_id`는 각각 unique

현재 SQLAlchemy 모델은 다음 차이가 있다.

- 없음.

Mission 금액 스냅샷 컬럼은 2026-06-01 기준 제거 대상이며 신규 API/모델에서 사용하지 않는다.

### Payment / Settlement

목표 정본에는 `payments`, `settlement_accounts`가 포함된다.

현재 저장소에는 Payment/Settlement 모델이 없고, `docs/generated/db-schema.md`의 `payments` 항목은 과거 목표안 형태와 다르다. Settlement 영역 구현 전에 목표 정본 기준으로 모델, 서비스, 마이그레이션 계획을 새로 작성해야 한다.

### Legacy Phone Verification

`phone_verifications`는 목표 정본에서 legacy 테이블이다.

현재 신규 인증 흐름은 `auth_phone_verifications`를 사용하며, `phone_verifications` 모델과 repository는 만들지 않는다. 단, 운영 DB나 migration 이력에 남은 테이블로 문서화한다.

### FK Constraint Policy

목표 정본은 실제 MySQL FK constraint를 두지 않는 정책이다. 현재 일부 SQLAlchemy 모델은 `ForeignKey`를 선언하고 있으므로, 앞으로 모델 정렬 시 다음 중 하나로 통일해야 한다.

1. DB FK constraint 없음 정책에 맞춰 SQLAlchemy `ForeignKey` 선언을 제거하고 인덱스/unique만 유지한다.
2. SQLAlchemy 관계 편의를 유지하되, 실제 migration에는 FK constraint를 만들지 않는 별도 규칙을 명시한다.

이 설계 문서의 기본 결정은 1번이다.

## 고려한 대안

### 현재 코드 기준 정본화

현재 구현과 가장 빨리 일치하지만, 결제/정산과 legacy 테이블 기준이 누락된다. 사용자가 제공한 전체 스키마를 반영하지 못하므로 선택하지 않는다.

### As-Is와 To-Be 완전 분리

불일치 설명은 가장 명확하지만, 이후 문서가 이중 기준을 참조할 위험이 있다. 이번에는 목표 정본을 하나로 정하고, 현재 코드는 갭으로만 기록한다.

## 롤아웃 또는 마이그레이션 메모

1. 이 문서를 기준으로 `docs/generated/db-schema.md`를 목표 정본 스냅샷으로 갱신한다.
2. 도메인별 `docs/exec-plans/active/*/model.md`에서 목표 정본과 다른 표현을 정리한다.
3. Mission 정렬 작업은 테스트로 현재 API 동작을 잠근 뒤 컬럼/타입/FK/unique 정책을 별도 마이그레이션 계획으로 진행한다.
4. Payment/Settlement 구현은 새 실행 계획에서 `payments`, `settlement_accounts` 모델과 integration test를 함께 정의한다.
5. 목표 정본 외 알림 보조 테이블은 별도 생성 스키마 섹션으로 분리해 핵심 정본과 섞이지 않게 한다.

## 리스크와 열린 질문

- 기존 테스트 DB는 `Base.metadata.create_all()`을 사용하므로 SQLAlchemy `ForeignKey` 제거 시 테스트 스키마 형태가 바뀐다.
- 실제 운영 MySQL에 이미 FK constraint가 만들어져 있다면 제거 migration이 필요할 수 있다.
- `payments`의 금액/상태/PG 응답 원문 보관 정책은 구현 전에 보안/개인정보 기준과 함께 재검토해야 한다.
- `settlement_accounts.encrypted_account_number`는 암호화 키 관리와 마스킹 규칙이 확정되어야 한다.
