# User/Auth Test Scenarios

기준 테스트 파일: `tests/test_user_auth_integration.py`, `tests/test_timestamps.py`

## 보장 범위

- 회원가입, 로그인, refresh token 갱신, 로그아웃의 기본 흐름을 검증한다.
- 개발 환경 인증 우회 코드 허용과 운영 환경 거부를 구분한다.
- 존재하지 않는 사용자, pending verification 없음, 코드 불일치 같은 인증 실패를 검증한다.
- 사용자 상세, 알림 설정, 닉네임 변경, FCM 토큰 저장 흐름을 검증한다.
- 회원 탈퇴는 soft delete, 원본정보 30일 snapshot 보관, 매칭 전 활동 자동 취소, 진행 중 활동 차단을 검증한다.
- SMS background 발송 실패가 verification 저장을 깨지 않는지 확인한다.
- 사용자/인증 문서 모델과 ORM timestamp 관리 규칙을 검증한다.
