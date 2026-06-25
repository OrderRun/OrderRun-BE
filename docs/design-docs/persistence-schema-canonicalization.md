# Persistence Schema Canonicalization

## 문제 정의

현재 저장소의 영속성 기준은 실제 SQLAlchemy 모델, 생성 스키마 스냅샷, 도메인/API 정본 문서에 나뉘어 있다.
이 문서는 목표 영속성 스키마의 기준과 현재 구현 갭을 한 곳에 고정한다.

## 결정 내용

목표 정본 테이블은 다음 기준을 사용한다.

| 테이블 | 담당 도메인 | 목표 ORM 매핑 | 설명 |
|--------|-------------|---------------|------|
| `users` | user/auth | O | 사용자 계정 |
| `auth_phone_verifications` | auth | O | 회원가입/로그인 전화번호 인증 |
| `phone_verifications` | user legacy | X | 구 전화번호 인증 테이블 |
| `user_fcm_tokens` | user | O | 사용자별 FCM 토큰 |
| `terms_agreements` | terms | O | 사용자별 필수 약관 동의 |
| `proposals` | bidding/proposal | O | 요청 모집 공고 |
| `offers` | bidding/offer | O | 러너 지원서와 수행 상태 |
| `dispute_evidences` | execution/dispute-evidence | O | 분쟁 사유 증빙 |
| `payments` | settlement | 목표 O / 현재 미구현 | 결제/정산 처리 |
| `settlement_accounts` | settlement | O | 러너 정산 계좌 |

관계는 애플리케이션 레벨에서 검증하며, 목표 정본 기준으로 실제 MySQL FK constraint는 두지 않는다.

```text
users 1 -> N proposals(orderer_id)
users 1 -> N offers(runner_id)
users 1 -> 1 user_fcm_tokens
users 1 -> 1 terms_agreements
users 1 -> 1 settlement_accounts

proposals 1 -> N offers
proposals 1 -> N dispute_evidences
offers 1 -> N dispute_evidences
offers 1 -> 1 payments
```

## 현재 확인 결과

| 영역 | 현재 상태 | 후속 조치 |
|------|-----------|-----------|
| User/Auth | 모델 있음 | 인덱스명과 감사 컬럼 규칙 유지 |
| Terms | 모델 있음 | 도메인/API 정본과 계속 정렬 |
| Proposal/Offer/DisputeEvidence | 모델 있음 | 상태 전이와 timestamp 규칙을 `domain.md`와 정렬 |
| Payment | 모델 없음 | 구현 전 모델/API/테스트 계획 작성 |
| Settlement Account | 모델 있음 | 암호화와 마스킹 정책 확정 필요 |
| Notification 보조 테이블 | 모델 있음 | 핵심 정본과 분리해 알림 도메인 문서에서 관리 |

## 규칙

- 공통 감사 컬럼은 ORM 대상 테이블에 `created_at`, `updated_at`을 둔다.
- DB default 대신 SQLAlchemy ORM의 `default`/`onupdate`에서 UTC timestamp를 채운다.
- 실제 DB FK constraint 없이 인덱스와 unique 제약, 서비스 검증으로 관계를 관리한다.
- API 계약은 [`../api-spec/README.md`](../api-spec/README.md), 상태 정책은 [`../domain.md`](../domain.md), 도메인별 테스트 보장은 [`../domains/README.md`](../domains/README.md)를 우선한다.

## 롤아웃 메모

1. 이 문서를 기준으로 [`../generated/db-schema.md`](../generated/db-schema.md)를 갱신한다.
2. Payment 구현 전 `payments` 모델, 서비스, API, 통합 테스트 계획을 작성한다.
3. Settlement 계좌 암호화 키 관리와 마스킹 규칙은 보안 기준과 함께 확정한다.
4. 알림 보조 테이블은 핵심 결제/수행 스키마와 섞지 않고 알림 도메인에서 관리한다.
