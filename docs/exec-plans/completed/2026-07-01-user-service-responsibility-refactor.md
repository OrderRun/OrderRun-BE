# 사용자 서비스 책임 분리

## 목표

`UserAuthService`에 결합된 전화번호 인증, 프로필, 탈퇴 책임을 분리하고 기존 API 동작과 트랜잭션 원자성을 유지한다.

## 반영 내용

- 전화번호 인증 저장·검증·SMS 등록을 `PhoneVerificationService`로 이동했다.
- 인증 유스케이스만 `UserAuthService`에 유지했다.
- 프로필 변경과 FCM 저장을 `UserProfileService`로 이동했다.
- 탈퇴 정책과 정리 절차를 `UserWithdrawalService`로 이동하고 전체 rollback을 보장했다.
- 라우터와 서비스 직접 호출 테스트를 새 경계로 전환했다.
- 공개 API와 DB 스키마는 변경하지 않았다.

## 검증

- `python -m compileall -q app/services app/api/v1 app/models`
- MySQL test compose 환경의 `tests/test_phone_verification.py`
- MySQL test compose 환경의 `tests/test_user_auth_integration.py`

## 남은 리스크

- FCM 토큰이 다중 기기 생명주기를 갖게 되면 별도 서비스로 분리해야 한다.
- 탈퇴가 관여하는 도메인이 추가되면 동일 트랜잭션과 차단 정책을 함께 확장해야 한다.
