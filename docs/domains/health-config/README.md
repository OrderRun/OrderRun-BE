# Health/Config Domain

Health/Config는 서버 health 응답과 설정 객체 로딩 규칙을 검증한다.

## 책임

- health endpoint가 v1 공통 응답 wrapper를 따른다.
- 필수 설정과 선택 설정의 로딩 기준을 분리한다.
- AWS SNS 설정 값이 환경에서 올바르게 매핑되는지 확인한다.

## 정본 링크

- 로컬 환경 설정: [`../../setup/local-development.md`](../../setup/local-development.md)
- 테스트 보장: [`test-scenarios.md`](./test-scenarios.md)
