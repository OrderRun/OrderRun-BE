# User/Auth Domain

User/Auth는 전화번호 기반 인증, 토큰 생명주기, 사용자 상세, 알림 설정, FCM 토큰을 담당한다.

## 책임

- 회원가입/로그인 인증 코드 발송과 확인을 처리한다.
- access/refresh token 발급, 갱신, 로그아웃을 처리한다.
- 사용자 상세, 알림 설정, FCM 토큰 저장 API의 사용자 식별 기준을 제공한다.
- SMS 실패와 개발/운영 환경별 인증 코드 우회 정책을 분리한다.

## 정본 링크

- API 계약: [`../../api-spec/README.md`](../../api-spec/README.md)의 Auth API와 User API
- 사용자 부가 정책: [`../../domain.md`](../../domain.md)의 정책 기준
- 테스트 보장: [`test-scenarios.md`](./test-scenarios.md)
