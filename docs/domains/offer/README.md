# Offer Domain

Offer는 러너가 Proposal에 제출하는 지원이며, 수락 이후 러너 관점 수행 상태의 기준이다.

## 책임

- Proposal에 대한 Offer 생성, 목록/상세/내 목록 조회, 수락, 취소를 담당한다.
- 수락된 Offer ID가 매칭 이후 수행 건의 기준 식별자다.
- 러너 완료, 러너 분쟁, 관리자 분쟁 해결은 Offer 상태와 timestamp를 갱신한다.
- 분쟁 사유는 DisputeEvidence에 남기고, 수행 상태 정본은 Proposal/Offer가 가진다.
- 러너 분쟁 접수 전 표시할 설문 질문은 `GET /v1/dispute-survey/questions?targetType=RUNNER`에서 조회한다.

## 정본 링크

- API 계약: [`../../api-spec/README.md`](../../api-spec/README.md)의 Offer API
- 상태/정책: [`../../domain.md`](../../domain.md)의 OfferStatus와 DisputeEvidence
- 테스트 보장: [`test-scenarios.md`](./test-scenarios.md)
