# API Contract/OpenAPI Domain

API Contract/OpenAPI는 모든 외부 API가 공통 응답 wrapper, error shape, 예시, 문서화 규칙을 따르는지 관리한다.

## 책임

- 성공 응답과 실패 응답의 표준 shape를 고정한다.
- OpenAPI metadata, operation 예시, request/response body 계약을 검증한다.
- 현재 공개 API 계약에 포함되지 않는 legacy endpoint가 다시 노출되지 않도록 회귀를 막는다.
- API DTO 간 상속 금지처럼 문서 생성 안정성에 필요한 규칙을 검증한다.

## 정본 링크

- API 계약: [`../../api-spec/README.md`](../../api-spec/README.md)
- 에러 계약: [`../../api-spec/README.md`](../../api-spec/README.md)의 공통 응답/에러 섹션
- 테스트 보장: [`test-scenarios.md`](./test-scenarios.md)
