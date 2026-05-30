# Terms Agreement Migration Spec

`terms-agreement`는 FastAPI 마이그레이션에서 User/Auth 다음에 옮길 사용자 부가 정책 도메인이다.

## 문서 구성

- [`requirements.md`](./requirements.md): 약관 동의 정책과 API별 acceptance criteria
- [`design.md`](./design.md): FastAPI 구현 설계와 책임 경계
- [`verification.md`](./verification.md): 기존 동작을 고정하는 검증 하네스
- [`model.md`](./model.md): `terms_agreements` 모델과 `TermsType` 구조

## 구현 순서

1. User/Auth의 current-user dependency와 공통 응답/에러 처리를 재사용한다.
2. `terms_agreements` 모델과 repository를 만든다.
3. `POST /v1/terms`를 구현한다.
4. 필수 약관 검증, 사용자 존재 검증, 사용자별 upsert를 통합 테스트로 고정한다.
