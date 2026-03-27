# Offer API

`Offer` 도메인의 엔티티 정의, API 스펙, 통합 테스트 기준 문서를 모아둔 디렉터리다.

## 문서 목록

- [offer-entity.md](./offer-entity.md): 엔티티 필드와 상태 규칙
- [offer-api-spec.md](./offer-api-spec.md): 목록/상세/생성/수정/삭제 중 필요한 API 스펙
- [offer-integration-test-plan.md](./offer-integration-test-plan.md): 통합 테스트 시나리오와 검증 포인트

## 개요

Offer는 Proposal(요청)에 대해 Runner가 제안하는 도메인입니다.

### 주요 기능
1. **Offer 생성**: Runner가 특정 Proposal에 제안을 제출
2. **Offer 목록 조회**: 특정 Proposal에 연결된 모든 Offer 조회

### 상태 전이
```
WAITING (생성 시 기본값)
  ├─→ ACCEPTED (수락됨)
  └─→ REJECTED (거절됨)
```

### 비즈니스 규칙
- 같은 Proposal에 같은 Runner는 한 번만 Offer를 생성할 수 있음
- Proposal 상태가 `POSTED` 또는 `OFFERED`일 때만 Offer 생성 가능
- 첫 Offer가 생성되면 Proposal 상태가 `POSTED` → `OFFERED`로 변경
