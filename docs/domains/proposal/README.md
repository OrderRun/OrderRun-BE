# Proposal Domain

Proposal은 오더러가 등록한 요청의 모집, 매칭, 오더러 관점 완료/분쟁 상태를 추적한다.

## 책임

- 요청 게시글 생성, 목록/상세/내 목록 조회, 수정, 매칭 전 취소를 담당한다.
- 공개 모집 중인 다른 사용자의 게시글 신고와, 관리자 신고 승인·반려를 담당한다.
- Offer가 생성되면 모집 상태가 `POSTED`에서 `OFFERED`로 전이된다.
- Offer 수락 이후 오더러 관점 진행 상태는 Proposal에서 추적한다.
- 오더러 완료 확인과 분쟁 접수는 수락된 Offer와 함께 상태를 맞춘다.
- 오더 분쟁 접수 전 표시할 설문 질문은 `GET /v1/dispute-survey/questions?targetType=ORDER`에서 조회한다.

## 정본 링크

- API 계약: [`../../api-spec/README.md`](../../api-spec/README.md)의 Proposal API
- 상태/정책: [`../../domain.md`](../../domain.md)의 ProposalStatus
- 테스트 보장: [`test-scenarios.md`](./test-scenarios.md)
