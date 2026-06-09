# User API Specification

User/Auth/Terms API의 외부 계약 정본은 [`../../api-spec/README.md`](../../api-spec/README.md)의 `Auth API`, `User API`, `Terms API` 섹션이다.

이 문서는 과거 도메인별 상세 명세 위치를 유지하기 위한 참조 문서다. 새 요청/응답 필드, 상태 코드, 인증 예외 규칙은 통합 API 명세를 우선한다.

## 포함 API

- `POST /v1/auth/signup/send`
- `POST /v1/auth/signup/confirm`
- `POST /v1/auth/login/send`
- `POST /v1/auth/login/confirm`
- `POST /v1/auth/refresh`
- `POST /v1/auth/logout`
- `GET /v1/user/detail`
- `POST /v1/user/alarm`
- `PATCH /v1/user/fcm-token`
- `POST /v1/terms`

## 참고

- 통합 API 명세: [`../../api-spec/README.md`](../../api-spec/README.md)
- User/Auth 도메인 문서: [`../../domains/user-auth/README.md`](../../domains/user-auth/README.md)
- Terms Agreement 도메인 문서: [`../../domains/terms-agreement/README.md`](../../domains/terms-agreement/README.md)
- 구현 갭: [`../../api-spec/implementation-gaps.md`](../../api-spec/implementation-gaps.md)
