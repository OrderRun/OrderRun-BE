# User/Auth Migration Spec

`user-auth`는 FastAPI 마이그레이션의 첫 번째 사용자 계정 도메인 묶음이다.

## 문서 구성

- [`user/requirements.md`](./user/requirements.md): 사용자 API 정책
- [`user/design.md`](./user/design.md): 사용자 API 구현 설계
- [`user/verification.md`](./user/verification.md): 사용자 API 검증 하네스
- [`auth/requirements.md`](./auth/requirements.md): 전화번호 인증/토큰 정책
- [`auth/design.md`](./auth/design.md): 인증/토큰 구현 설계
- [`auth/verification.md`](./auth/verification.md): 인증/토큰 검증 하네스

## 구현 순서

1. 공통 응답, 예외, 현재 사용자 주입, JWT 검증 기반을 먼저 만든다.
2. `user` 도메인의 `detail`, `alarm`, `fcm-token` API를 구현한다.
3. `auth` 도메인의 `signup`, `login`, `refresh`, `logout` API를 구현한다.
4. 현재 Java 구현과 동일한 응답, 상태 코드, 전화번호 정규화, 토큰 규칙을 맞춘다.
