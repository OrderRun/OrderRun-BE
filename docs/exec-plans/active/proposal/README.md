# Proposal Migration Spec

`proposal-migration`은 FastAPI 마이그레이션에서 Bidding context의 첫 번째 핵심 도메인이다.

## 문서 구성

- [`requirements.md`](./requirements.md): Proposal API 정책과 acceptance criteria
- [`design.md`](./design.md): 구현 책임 경계와 상태 전이 설계
- [`verification.md`](./verification.md): Java baseline 기준 검증 하네스
- [`model.md`](./model.md): `proposals` 모델과 `ProposalStatus` 구조

## 구현 순서

1. User/Auth current-user dependency와 공통 응답/에러 처리를 재사용한다.
2. `Proposal` 모델, repository, 상태 enum을 만든다.
3. 목록/상세/내 목록 조회를 먼저 구현한다.
4. 생성/수정/취소와 상태 전이를 구현한다.
5. Offer 연동은 `own` 응답과 `OFFERED` 취소 시 WAITING Offer 거절까지만 연결한다.
