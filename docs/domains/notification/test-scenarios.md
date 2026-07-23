# Notification/SMS Test Scenarios

기준 테스트 파일: `tests/test_notification_integration.py`, `tests/test_sms_service.py`

## 보장 범위

- root 응답의 OpenAPI 예시 shape를 확인한다.
- 알림 목록, 통계, 상세 조회, 읽음 처리를 검증한다.
- 알림 발송 성공과 실패 응답을 검증한다.
- 지원, 수락, 만남 확인, 분쟁 이벤트가 수신자의 `alarm_enabled` 조건에 따라 `PENDING` 또는 `SKIPPED` 알림 레코드를 생성하는지 검증한다.
- 알림 발송 worker는 실제 FCM을 호출하지 않고 fake FCM service의 `send_notification()` 호출 여부, 전달 data, `SENT`/`FAILED` 상태 전이를 검증한다.
- 알림 발송 worker가 `SKIPPED` 알림을 FCM으로 보내거나 상태 변경하지 않는지 검증한다.
- AWS SNS 전화번호 포맷, SMS attributes, provider error 전파를 검증한다.

## 비보장 범위

- Firebase Admin SDK와 외부 FCM 네트워크 발송은 통합 테스트에서 실행하지 않는다.
- 모바일 OS의 실제 수신, 배지, 사운드, 클릭 동작은 백엔드 테스트 범위가 아니다.
