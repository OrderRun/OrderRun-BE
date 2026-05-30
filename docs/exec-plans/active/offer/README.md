# Offer Migration Spec

`offer-migration`은 FastAPI 마이그레이션에서 Proposal 다음에 옮길 Bidding context 도메인이다.

## 문서 구성

- [`requirements.md`](./requirements.md): Offer API 정책과 acceptance criteria
- [`design.md`](./design.md): 구현 책임 경계와 상태 전이 설계
- [`verification.md`](./verification.md): Java baseline 기준 검증 하네스
- [`model.md`](./model.md): `offers` 모델과 `OfferStatus` 구조

## 구현 순서

1. Proposal model/status/repository가 먼저 준비되어 있어야 한다.
2. Offer model/status/repository를 만든다.
3. 생성, 상세, Proposal별 목록, 내 목록, 취소 API를 구현한다.
4. Offer 수락 API에서 Mission 생성과 Proposal/Offer 상태 전이를 단일 트랜잭션으로 묶는다.
