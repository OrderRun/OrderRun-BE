# Admin/Payment/Settlement Test Scenarios

기준 테스트 파일: `tests/test_admin_integration.py`

## 보장 범위

- 결제 확인은 request body 없이 `HOLDING` Proposal을 공개 상태로 전환한다.
- 결제 확인은 `HOLDING`이 아닌 Proposal을 거부한다.
- 정산 확정은 완료 상태의 Offer만 처리한다.
- 분쟁 해결은 분쟁 상태의 Offer를 `RESOLVED`로 전이한다.
