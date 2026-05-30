# Mission Migration Spec

`mission-migration`은 FastAPI 마이그레이션에서 Offer 수락 이후의 Execution context를 옮기는 도메인이다.

## 문서 구성

- [`requirements.md`](./requirements.md): Mission API 정책과 acceptance criteria
- [`design.md`](./design.md): 구현 책임 경계와 상태 전이 설계
- [`verification.md`](./verification.md): Java baseline 기준 검증 하네스
- [`model.md`](./model.md): `missions` 모델과 `MissionStatus` 구조

## 구현 순서

1. User/Auth current-user dependency, Proposal, Offer migration 결과를 재사용한다.
2. Mission model/status/repository를 만든다.
3. Offer 수락 API에서 Mission 생성과 Proposal/Offer 상태 전이를 단일 트랜잭션으로 구현한다.
4. 내 Mission 목록 조회를 role/status 필터와 PageResponse로 구현한다.
5. Mission 상태 업데이트와 완료 시 Offer 완료 연동을 구현한다.
