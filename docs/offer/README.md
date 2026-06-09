# Offer API

`Offer` 도메인의 과거 상세 문서 위치를 유지하는 디렉터리다.
현재 도메인 개념과 테스트 보장 범위는 [`../domains/offer/`](../domains/offer/)를 우선한다.

## 문서 목록

- [offer-entity.md](./offer-entity.md): 엔티티 필드와 상태 규칙
- [offer-api-spec.md](./offer-api-spec.md): 목록/상세/생성/수정/삭제 중 필요한 API 스펙
- [offer-integration-test-plan.md](./offer-integration-test-plan.md): 통합 테스트 시나리오와 검증 포인트

## 개요

Offer는 Proposal(요청)에 대해 Runner가 제안하는 도메인입니다.

### 주요 기능
1. **Offer 생성**: Runner가 특정 Proposal에 제안을 제출
2. **Offer 조회**: Proposal별 목록, 상세, 내 목록 조회
3. **Offer 수락**: Proposal 작성자가 Offer를 수락하고 수락된 Offer를 수행 건 기준으로 확정
4. **Offer 수행 상태 추적**: Runner 전달 완료와 분쟁 접수
5. **Offer 취소**: Runner가 본인의 대기 Offer 취소

### 상태 전이
```
WAITING (생성 시 기본값)
  ├─→ ACCEPTED (수락됨)
  ├─→ REJECTED (거절됨)
  └─→ CANCELLED (러너 취소)
ACCEPTED
  ├─→ RUNNER_COMPLETED (러너 완료)
  └─→ DISPUTED (분쟁 접수)
RUNNER_COMPLETED
  ├─→ ALL_COMPLETED (오더러 완료도 접수됨)
  └─→ DISPUTED (분쟁 접수)
ALL_COMPLETED
  └─→ DISPUTED (분쟁 접수)
DISPUTED
  └─→ REFUNDED (환불 완료)
```

### 비즈니스 규칙
- 같은 Proposal에 같은 Runner는 한 번만 Offer를 생성할 수 있음
- Proposal 상태가 `POSTED` 또는 `OFFERED`일 때만 Offer 생성 가능
- 첫 Offer가 생성되면 Proposal 상태가 `POSTED` → `OFFERED`로 변경
- 매칭 이후 러너 관점 수행 상태는 Offer에서 추적
- 완료 증빙과 분쟁 사유는 Proof에 기록
