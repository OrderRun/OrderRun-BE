# Settlement Account Domain

Settlement Account는 러너 또는 사용자에게 종속된 정산 계좌 정보를 관리한다.

## 책임

- 등록된 정산 계좌가 없을 때 null 응답을 제공한다.
- 계좌 정보를 저장하고 이후 같은 사용자 기준으로 수정한다.
- 정산 계좌 등록에 사용할 수 있는 은행명 목록을 제공한다.
- 인증과 입력 validation 규칙을 API 계약과 맞춘다.

## 정본 링크

- API 계약: [`../../api-spec/README.md`](../../api-spec/README.md)의 Settlement API
- 테스트 보장: [`test-scenarios.md`](./test-scenarios.md)
