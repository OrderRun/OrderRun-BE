# 생성 DB 스키마 스냅샷

## 목적

이 문서는 목표 영속성 스키마의 파생 스냅샷이다.
정본 결정은 [`docs/design-docs/persistence-schema-canonicalization.md`](../design-docs/persistence-schema-canonicalization.md)를 따른다.

현재 코드와 다른 항목은 구현 완료 상태가 아니라 목표 정본 또는 legacy 기준으로 기록한다.

## 전체 테이블

| 테이블 | 담당 도메인 | ORM 매핑 | 세부 문서 | 설명 |
|--------|-------------|----------|-----------|------|
| `users` | user/auth | O | `docs/domains/user-auth/README.md` | 사용자 계정 |
| `withdrawn_user_snapshots` | user/auth | O | `docs/domains/user-auth/withdrawal-policy.md` | 탈퇴 사용자 원본 정보 30일 임시 보관 |
| `auth_phone_verifications` | auth | O | `docs/domains/user-auth/README.md` | 회원가입/로그인 전화번호 인증 |
| `phone_verifications` | user legacy | X | 이 문서 | 구 전화번호 인증 테이블. 현재 코드 미사용 |
| `user_fcm_tokens` | user | O | `docs/domains/user-auth/README.md` | 사용자별 FCM 토큰 |
| `terms_agreements` | terms | O | `docs/exec-plans/completed/terms-agreement/model.md` | 사용자별 필수 약관 동의 |
| `proposals` | bidding/proposal | O | `docs/exec-plans/completed/proposal/model.md` | 심부름 모집 공고 |
| `offers` | bidding/offer | O | `docs/domains/offer/README.md` | 러너 지원서 |
| `proofs` | execution/proof | O | `docs/domain.md` | 배송 사진/분쟁 사유 증빙 |
| `dispute_survey_questions` | dispute-survey | O | `docs/api-spec/README.md` | 분쟁 접수 전 설문 질문 마스터 |
| `payments` | settlement | 목표 O / 현재 미구현 | 이 문서 | 결제/정산 처리 |
| `settlement_accounts` | settlement | O | 이 문서 | 러너 정산 계좌 |

## 관계 요약

```text
users 1 -> N proposals(orderer_id)
users 1 -> N offers(runner_id)
users 1 -> 1 user_fcm_tokens
users 1 -> 1 terms_agreements
users 1 -> 1 settlement_accounts
users 1 -> N withdrawn_user_snapshots

proposals 1 -> N offers
proposals 1 -> N proofs
offers 1 -> N proofs
offers 1 -> 1 payments
```

위 관계는 애플리케이션 레벨 관계다. 목표 정본 기준으로 실제 MySQL FK constraint는 없다.

## 공통 컬럼 규칙

| 컬럼 | 타입 | Null | 설명 |
|------|------|------|------|
| `created_at` | `datetime(6)` | NO | 생성 시각 |
| `updated_at` | `datetime(6)` | NO | 수정 시각 |

예외 없이 모든 현재 ORM 대상 테이블은 위 감사 컬럼을 가진다.
Legacy `phone_verifications`도 migration 기준으로 감사 컬럼이 있다.

## `users`

| 컬럼 | 타입 | Null | 키/인덱스 | 설명 |
|------|------|------|-----------|------|
| `id` | `varchar(36)` | NO | PK | 사용자 UUID |
| `password_hash` | `varchar(255)` | YES |  | 비밀번호 해시. 현재 phone-auth 흐름에서는 null 가능 |
| `name` | `varchar(100)` | NO |  | 사용자 이름 |
| `phone` | `varchar(20)` | YES | UNIQUE `uk_users_phone` | 정규화된 전화번호 |
| `phone_verified_at` | `datetime(6)` | YES |  | 전화번호 인증 완료 시각 |
| `last_login_at` | `datetime(6)` | YES |  | 마지막 로그인 시각 |
| `alarm_enabled` | `boolean` | NO |  | 알림 수신 동의 여부 |
| `level` | `integer` | NO |  | 성공 완료한 러너 Offer 수 기반 레벨 |
| `deleted` | `boolean` | NO | INDEX `idx_users_deleted` | 탈퇴 여부 |
| `deleted_at` | `datetime(6)` | YES |  | 탈퇴 처리 시각 |
| `created_at` | `datetime(6)` | NO |  | 생성 시각 |
| `updated_at` | `datetime(6)` | NO |  | 수정 시각 |

메모:

- `id`는 애플리케이션에서 UUID로 생성한다.
- `phone`은 하이픈/공백 제거 및 `+82` -> `0` 변환 후 저장한다.
- 탈퇴 시 `deleted = true`, `phone = null`, `name = '탈퇴한 사용자'`로 soft delete 처리한다.

## `withdrawn_user_snapshots`

| 컬럼 | 타입 | Null | 키/인덱스 | 설명 |
|------|------|------|-----------|------|
| `id` | `bigint` | NO | PK, auto increment | 탈퇴 snapshot row ID |
| `user_id` | `varchar(36)` | NO | INDEX `idx_withdrawn_user_snapshots_user_id` | 탈퇴 사용자 ID |
| `name` | `varchar(100)` | YES |  | 탈퇴 전 사용자 이름 |
| `phone` | `varchar(20)` | YES | INDEX `idx_withdrawn_user_snapshots_phone` | 탈퇴 전 전화번호 |
| `phone_verified_at` | `datetime(6)` | YES |  | 탈퇴 전 전화번호 인증 시각 |
| `last_login_at` | `datetime(6)` | YES |  | 탈퇴 전 마지막 로그인 시각 |
| `user_created_at` | `datetime(6)` | YES |  | 탈퇴 전 가입 시각 |
| `withdrawn_at` | `datetime(6)` | NO | INDEX `idx_withdrawn_user_snapshots_withdrawn_at` | 탈퇴 처리 시각 |
| `anonymize_after` | `datetime(6)` | NO | INDEX `idx_withdrawn_user_snapshots_anonymize_after` | 익명화 예정 시각 |
| `anonymized_at` | `datetime(6)` | YES |  | 익명화 완료 시각 |
| `created_at` | `datetime(6)` | NO |  | 생성 시각 |
| `updated_at` | `datetime(6)` | NO |  | 수정 시각 |

메모:

- 탈퇴 원본 정보는 고객센터/분쟁 대응 목적으로 30일간 임시 보관한다.
- `anonymize_after`가 지난 row는 배치에서 개인정보 필드를 null로 익명화한다.

## `auth_phone_verifications`

| 컬럼 | 타입 | Null | 키/인덱스 | 설명 |
|------|------|------|-----------|------|
| `id` | `bigint` | NO | PK, auto increment | 인증 요청 ID |
| `purpose` | `varchar(20)` | NO | `idx_auth_phone_verifications_purpose_phone_status_expires`, `idx_auth_phone_verifications_purpose_phone_status` | `SIGNUP`, `LOGIN` |
| `phone` | `varchar(20)` | NO | 같은 복합 인덱스 | 정규화된 전화번호 |
| `name` | `varchar(100)` | YES |  | 회원가입 요청 이름 |
| `carrier` | `varchar(50)` | YES |  | 통신사 |
| `code_hash` | `varchar(100)` | NO |  | 인증 코드 해시 |
| `status` | `varchar(20)` | NO | 같은 복합 인덱스 | `PENDING`, `VERIFIED`, `EXPIRED` |
| `expires_at` | `datetime(6)` | NO | 같은 복합 인덱스 | 만료 시각 |
| `sent_at` | `datetime(6)` | NO |  | 발송 시각 |
| `verified_at` | `datetime(6)` | YES |  | 인증 완료 시각 |
| `attempt_count` | `integer` | NO |  | 코드 확인 실패 횟수 |
| `created_at` | `datetime(6)` | NO |  | 생성 시각 |
| `updated_at` | `datetime(6)` | NO |  | 수정 시각 |

현재 코드 메모:

- SQLAlchemy 인덱스명은 `idx_auth_phone_verifications_purpose_phone_status_expires_at`로 선언되어 있다.
- `created_at`, `updated_at`은 DB default 없이 ORM에서 insert/update 시 채운다.

## `phone_verifications`

| 컬럼 | 타입 | Null | 키/인덱스 | 설명 |
|------|------|------|-----------|------|
| `id` | `bigint` | NO | PK, auto increment | 인증 요청 ID |
| `user_id` | `varchar(36)` | NO | `idx_phone_verifications_user_status_expires` | 사용자 ID |
| `phone` | `varchar(20)` | NO | `idx_phone_verifications_phone_status` | 인증 대상 전화번호 |
| `code_hash` | `varchar(100)` | NO |  | 인증 코드 해시 |
| `status` | `varchar(20)` | NO | 복합 인덱스 | 인증 상태 |
| `expires_at` | `datetime(6)` | NO | 복합 인덱스 | 만료 시각 |
| `sent_at` | `datetime(6)` | NO |  | 발송 시각 |
| `verified_at` | `datetime(6)` | YES |  | 인증 완료 시각 |
| `attempt_count` | `integer` | NO |  | 코드 확인 실패 횟수 |
| `created_at` | `datetime(6)` | NO |  | 생성 시각 |
| `updated_at` | `datetime(6)` | NO |  | 수정 시각 |

메모:

- Legacy 전화번호 인증 테이블이다.
- 현재 ORM 모델과 repository가 없으며, 신규 인증 흐름은 `auth_phone_verifications`를 사용한다.

## `user_fcm_tokens`

| 컬럼 | 타입 | Null | 키/인덱스 | 설명 |
|------|------|------|-----------|------|
| `id` | `bigint` | NO | PK, auto increment | 토큰 row ID |
| `user_id` | `varchar(36)` | NO | UNIQUE `uk_user_fcm_tokens_user_id` | 사용자 ID |
| `fcm_token` | `varchar(4096)` | NO |  | FCM 등록 토큰 |
| `created_at` | `datetime(6)` | NO |  | 생성 시각 |
| `updated_at` | `datetime(6)` | NO |  | 수정 시각 |

## `terms_agreements`

| 컬럼 | 타입 | Null | 키/인덱스 | 설명 |
|------|------|------|-----------|------|
| `id` | `bigint` | NO | PK, auto increment | 약관 동의 row ID |
| `user_id` | `varchar(36)` | NO | UNIQUE `uk_terms_agreements_user_id`, INDEX `idx_terms_agreements_user_id` | 사용자 ID |
| `terms_of_service` | `boolean` | NO |  | 이용약관 동의 |
| `privacy_policy` | `boolean` | NO |  | 개인정보처리방침 동의 |
| `payment_refund_policy` | `boolean` | NO |  | 결제/환불지급정책 동의 |
| `agreed_at` | `datetime(6)` | NO |  | 동의 시각 |
| `created_at` | `datetime(6)` | NO |  | 생성 시각 |
| `updated_at` | `datetime(6)` | NO |  | 수정 시각 |

## `proposals`

| 컬럼 | 타입 | Null | 키/인덱스 | 설명 |
|------|------|------|-----------|------|
| `id` | `bigint` | NO | PK, auto increment | 공고 ID |
| `orderer_id` | `varchar(36)` | NO | INDEX `idx_proposals_orderer_id` | 요청 작성자 사용자 ID |
| `title` | `varchar(50)` | NO |  | 공고 제목 |
| `content` | `varchar(500)` | NO |  | 요청 상세 내용 |
| `deadline` | `datetime(6)` | NO |  | UTC 기준 수행 마감 시각 |
| `meeting_at` | `datetime(6)` | NO |  | legacy 호환 컬럼. 현재 API 미노출 |
| `errand_fee` | `integer` | NO |  | 심부름비 |
| `item_price` | `integer` | NO |  | legacy 호환 컬럼. 현재 API 미노출 |
| `deposit` | `integer` | NO |  | legacy 호환 컬럼. 현재 API 미노출 |
| `status` | `varchar(20)` | NO |  | `HOLDING`, `POSTED`, `OFFERED`, `MATCHED`, `ORDER_COMPLETED`, `ALL_COMPLETED`, `DISPUTED`, `RESOLVED`, `CANCELLED` |
| `created_at` | `datetime(6)` | NO |  | 생성 시각 |
| `matched_at` | `datetime(6)` | YES |  | Offer 수락으로 매칭된 시각 |
| `delivery_reported_at` | `datetime(6)` | YES |  | 러너 완료가 Proposal에 반영된 시각 |
| `received_confirmed_at` | `datetime(6)` | YES |  | 오더러 완료 확인 시각 |
| `settled_at` | `datetime(6)` | YES |  | legacy 호환 컬럼. 현재 API 미노출 |
| `disputed_at` | `datetime(6)` | YES |  | 분쟁 접수 시각 |
| `resolved_at` | `datetime(6)` | YES |  | 분쟁 해결 시각 |
| `updated_at` | `datetime(6)` | NO |  | 수정 시각 |

## `offers`

| 컬럼 | 타입 | Null | 키/인덱스 | 설명 |
|------|------|------|-----------|------|
| `id` | `bigint` | NO | PK, auto increment | Offer ID |
| `proposal_id` | `bigint` | NO | UNIQUE `uk_proposal_runner` 일부 | 대상 Proposal ID |
| `runner_id` | `varchar(36)` | NO | UNIQUE `uk_proposal_runner` 일부, INDEX `idx_offers_runner_id` | 지원자 사용자 ID |
| `status` | `varchar(20)` | NO |  | `WAITING`, `ACCEPTED`, `RUNNER_COMPLETED`, `ALL_COMPLETED`, `DISPUTED`, `RESOLVED`, `REJECTED`, `CANCELLED` |
| `open_chat_url` | `varchar(500)` | YES |  | 매칭 당사자에게 노출할 카카오톡 오픈채팅방 링크 |
| `created_at` | `datetime(6)` | NO |  | 생성 시각 |
| `accepted_at` | `datetime(6)` | YES |  | 오더가 Offer를 수락한 시각 |
| `delivery_completed_at` | `datetime(6)` | YES |  | 러너 완료 시각 |
| `receipt_confirmed_at` | `datetime(6)` | YES |  | 오더러 완료 확인이 Offer에 반영된 시각 |
| `settled_at` | `datetime(6)` | YES |  | legacy 호환 컬럼. 현재 API 미노출 |
| `disputed_at` | `datetime(6)` | YES |  | 분쟁 접수 시각 |
| `resolved_at` | `datetime(6)` | YES |  | 분쟁 해결 시각 |
| `updated_at` | `datetime(6)` | NO |  | 수정 시각 |

## `proofs`

| 컬럼 | 타입 | Null | 키/인덱스 | 설명 |
|------|------|------|-----------|------|
| `id` | `bigint` | NO | PK, auto increment | Proof ID |
| `proposal_id` | `bigint` | NO | INDEX `idx_proofs_proposal_id` | 연관 Proposal ID |
| `offer_id` | `bigint` | NO | INDEX `idx_proofs_offer_id` | 연관 Offer ID |
| `actor_id` | `varchar(36)` | NO |  | 증빙 작성 사용자 ID |
| `proof_type` | `varchar(30)` | NO | INDEX `idx_proofs_proof_type` | `DELIVERY`, `DISPUTE` |
| `image_url` | `varchar(500)` | YES |  | 배송 사진 URL |
| `reason` | `text` | YES |  | 분쟁 사유 |
| `survey_question_id` | `bigint` | YES | INDEX `idx_proofs_survey_question_id` | 선택한 분쟁 설문 질문 ID |
| `created_at` | `datetime(6)` | NO |  | 생성 시각 |

현재 코드 갭:

- 없음.

## `dispute_survey_questions`

| 컬럼 | 타입 | Null | 키/인덱스 | 설명 |
|------|------|------|-----------|------|
| `id` | `bigint` | NO | PK, auto increment | 질문 ID |
| `target_type` | `varchar(6)` | NO | UNIQUE `uk_dispute_survey_questions_target_order` 일부, INDEX `idx_dispute_survey_questions_lookup` | `ORDER`, `RUNNER` |
| `question_text` | `varchar(500)` | NO |  | 질문 내용 |
| `display_order` | `integer` | NO | UNIQUE `uk_dispute_survey_questions_target_order` 일부, INDEX `idx_dispute_survey_questions_lookup` | 클라이언트 표시 순서 |
| `is_active` | `boolean` | NO | INDEX `idx_dispute_survey_questions_lookup` | 조회 노출 여부 |
| `created_at` | `datetime(6)` | NO |  | 생성 시각 |
| `updated_at` | `datetime(6)` | NO |  | 수정 시각 |

현재 코드 메모:

- 분쟁 접수 API는 `surveyQuestionId`와 `disputeReason`을 필수로 받는다.
- `GET /v1/dispute-survey/questions`는 active 질문만 대상별 순서대로 반환한다.

## `payments`

| 컬럼 | 타입 | Null | 키/인덱스 | 설명 |
|------|------|------|-----------|------|
| `id` | `bigint` | NO | PK, auto increment | Payment ID |
| `offer_id` | `bigint` | NO | UNIQUE `uk_offer_id` | 정산 대상 Offer ID |
| `orderer_id` | `varchar(36)` | NO | INDEX `idx_payments_orderer_id` | 요청자 사용자 ID 스냅샷 |
| `runner_id` | `varchar(36)` | NO | INDEX `idx_payments_runner_id` | 수행자 사용자 ID 스냅샷 |
| `run_fee` | `decimal(10,2)` | NO |  | 수행 수수료 |
| `item_price` | `decimal(10,2)` | NO |  | 물품 금액 |
| `total_amount` | `decimal(10,2)` | NO |  | 총 결제 금액 |
| `settlement_amount` | `decimal(10,2)` | NO |  | 러너 정산 금액 |
| `pg_transaction_id` | `varchar(100)` | YES |  | PG 거래 ID |
| `pg_response` | `text` | YES |  | PG 응답 원문 |
| `status` | `varchar(20)` | NO |  | `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `REFUNDED` |
| `processing_started_at` | `datetime(6)` | YES |  | 결제 처리 시작 시각 |
| `completed_at` | `datetime(6)` | YES |  | 결제 완료 시각 |
| `failed_at` | `datetime(6)` | YES |  | 결제 실패 시각 |
| `refunded_at` | `datetime(6)` | YES |  | 환불 완료 시각 |
| `failure_reason` | `text` | YES |  | 실패 사유 |
| `retry_count` | `integer` | NO |  | 결제 재시도 횟수 |
| `created_at` | `datetime(6)` | NO |  | 생성 시각 |
| `updated_at` | `datetime(6)` | NO |  | 수정 시각 |

현재 코드 메모:

- `payments` ORM 모델은 아직 없다.
- 기존 문서의 `payer_id`, `payee_id`, `amount`, `currency`, `provider`, `external_tx_id` 기준은 이 목표 정본으로 대체한다.

## `settlement_accounts`

| 컬럼 | 타입 | Null | 키/인덱스 | 설명 |
|------|------|------|-----------|------|
| `id` | `bigint` | NO | PK, auto increment | 정산 계좌 row ID |
| `user_id` | `varchar(36)` | NO | UNIQUE `uk_settlement_accounts_user_id`, INDEX `idx_settlement_accounts_user_id` | 계좌 소유 사용자 ID |
| `bank_name` | `varchar(50)` | NO |  | 은행명 |
| `account_holder` | `varchar(100)` | NO |  | 계좌주명 |
| `encrypted_account_number` | `varchar(500)` | NO |  | 암호화된 계좌번호 |
| `masked_account_number` | `varchar(50)` | NO |  | 표시용 마스킹 계좌번호 |
| `created_at` | `datetime(6)` | NO |  | 생성 시각 |
| `updated_at` | `datetime(6)` | NO |  | 수정 시각 |

현재 코드 메모:

- `settlement_accounts` ORM 모델은 `app/models/settlement.py`에 있다.
- 운영 전 `encrypted_account_number` 저장 방식은 KMS 또는 별도 암호화 유틸로 교체해야 한다.

## 목표 정본 외 현재 보조 테이블

아래 테이블은 현재 코드에 있지만 핵심 목표 정본 10개 테이블에는 포함하지 않는다. 별도 알림 문서에서 관리한다.

| 테이블 | 모델 | 설명 |
|--------|------|------|
| `device_tokens` | `app/models/notification.py` | 다중 디바이스 FCM 토큰 |
| `notifications` | `app/models/notification.py` | 알림 발송/상태 로그 |
| `notification_preferences` | `app/models/notification.py` | 사용자 알림 선호 설정 |

## 기준 문서

- [`docs/design-docs/persistence-schema-canonicalization.md`](../design-docs/persistence-schema-canonicalization.md)
- [`docs/domain.md`](../domain.md)
- [`docs/domains/README.md`](../domains/README.md)
