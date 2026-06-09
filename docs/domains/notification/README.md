# Notification/SMS Domain

Notification/SMS는 사용자 알림 조회/읽음 처리와 SMS provider 연동을 담당한다.

## 책임

- 알림 목록, 통계, 상세 조회, 읽음 처리를 제공한다.
- 알림 발송 성공과 실패 케이스를 API 계약에 맞춘다.
- AWS SNS 발송 형식, 속성, provider error 전파를 서비스 단위에서 검증한다.

## 정본 링크

- 제품 정책: [`../../product-specs/notification-policy.md`](../../product-specs/notification-policy.md)
- API 계약: [`../../api-spec/README.md`](../../api-spec/README.md)의 Notification API
- 테스트 보장: [`test-scenarios.md`](./test-scenarios.md)
