# Notification/SMS Test Scenarios

기준 테스트 파일: `tests/test_notification_integration.py`, `tests/test_sms_service.py`

## 보장 범위

- root 응답의 OpenAPI 예시 shape를 확인한다.
- 알림 목록, 통계, 상세 조회, 읽음 처리를 검증한다.
- 알림 발송 성공과 실패 응답을 검증한다.
- AWS SNS 전화번호 포맷, SMS attributes, provider error 전파를 검증한다.
