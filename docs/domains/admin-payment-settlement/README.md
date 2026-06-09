# Admin/Payment/Settlement Domain

Admin/Payment/Settlement는 관리자 결제 확정, 정산 확정, 환불 처리를 담당한다.

## 책임

- 입금 확인 대기 Proposal을 공개 상태로 전환한다.
- 완료된 Offer의 정산 확정을 처리한다.
- 분쟁 Offer의 환불 완료를 처리한다.
- 관리자 API는 일반 사용자 수행 상태와 정산 상태를 깨지 않도록 상태 조건을 검증한다.

## 정본 링크

- API 계약: [`../../api-spec/README.md`](../../api-spec/README.md)의 Admin API
- 상태/정책: [`../../domain.md`](../../domain.md)
- 테스트 보장: [`test-scenarios.md`](./test-scenarios.md)
