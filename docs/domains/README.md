# Domain Documentation

이 디렉터리는 OrderRun의 도메인별 개념과 테스트 보장 범위를 모아둔다.

## 정본 관계

- 외부 HTTP 요청/응답 계약 정본: [`../api-spec/README.md`](../api-spec/README.md)
- 상태 전이와 정책 정본: [`../domain.md`](../domain.md)
- 실제 테스트 위치: `tests/`

도메인별 문서는 사람이 읽는 해석 문서다. API 필드, 상태 enum, 에러 코드가 바뀌면 정본 문서를 먼저 갱신하고, 이 디렉터리의 도메인 문서는 그 변경의 의미와 테스트 보장 범위를 설명한다.
테스트 파일 목록과 함수 수는 `rg --files tests | sort`, `rg -n "^(def test_|async def test_)" tests | wc -l`로 확인한다.

## 도메인 목록

| 도메인 | 개념 문서 | 테스트 보장 |
|--------|-----------|-------------|
| Proposal | [`proposal/README.md`](./proposal/README.md) | [`proposal/test-scenarios.md`](./proposal/test-scenarios.md) |
| Offer | [`offer/README.md`](./offer/README.md) | [`offer/test-scenarios.md`](./offer/test-scenarios.md) |
| User/Auth | [`user-auth/README.md`](./user-auth/README.md) | [`user-auth/test-scenarios.md`](./user-auth/test-scenarios.md) |
| Terms Agreement | [`terms-agreement/README.md`](./terms-agreement/README.md) | [`terms-agreement/test-scenarios.md`](./terms-agreement/test-scenarios.md) |
| Settlement Account | [`settlement/README.md`](./settlement/README.md) | [`settlement/test-scenarios.md`](./settlement/test-scenarios.md) |
| Notification/SMS | [`notification/README.md`](./notification/README.md) | [`notification/test-scenarios.md`](./notification/test-scenarios.md) |
| Admin/Payment/Settlement | [`admin-payment-settlement/README.md`](./admin-payment-settlement/README.md) | [`admin-payment-settlement/test-scenarios.md`](./admin-payment-settlement/test-scenarios.md) |
| API Contract/OpenAPI | [`api-contract/README.md`](./api-contract/README.md) | [`api-contract/test-scenarios.md`](./api-contract/test-scenarios.md) |
| Health/Config | [`health-config/README.md`](./health-config/README.md) | [`health-config/test-scenarios.md`](./health-config/test-scenarios.md) |
