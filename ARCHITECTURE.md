# OrderRun-BE 아키텍처

## 목적

이 문서는 백엔드 시스템과 문서 하네스의 최상위 지도다.
제품 흐름, 시스템 경계, 어떤 종류의 결정이 어디에 기록되어야 하는지 빠르게 파악할 때 사용한다.

## 시스템 개요

`OrderRun`은 요청 등록, 제안 경쟁, 수락된 Offer 기반 수행, 결제 정산으로 이어지는 매칭 플랫폼 백엔드다.

핵심 컨텍스트:

- `User`: 사용자 식별, 프로필, 역할, 약관 동의 상태
- `Proposal`: 요청 생성과 공개
- `Offer`: 수행자의 제안 등록과 경쟁
- `Proof`: 수행 완료 증빙과 분쟁 사유 기록
- `Payment`: 결제 승인, 확정, 환불, 정산 기록

현재 기술 방향:

- Language: Python 3.12
- Framework: FastAPI
- Database: MySQL 8.x
- ORM: SQLAlchemy 2.x
- Validation: Pydantic 2.x

## 코드와 기준 문서

현재 구현 코드는 `app/` 아래에 최소 부트스트랩 형태로 존재한다.
현재 기준은 아래 문서 세트에 정리되어 있다.

- [`docs/api-spec/README.md`](./docs/api-spec/README.md): 외부 API 요청/응답 계약 정본
- [`docs/domain.md`](./docs/domain.md): 도메인 상태와 정책 정본
- [`docs/domains/README.md`](./docs/domains/README.md): 도메인별 개념과 테스트 보장 문서

## 문서 하네스 구조

`docs/` 트리는 시간순이 아니라 결정 종류별로 나눈다.

### 하네스 엔지니어링 가이드
- [`docs/HARNESS_ENGINEERING.md`](./docs/HARNESS_ENGINEERING.md): 문서 중심 개발 방법론 전체
- [`docs/DIRECTORY_STRUCTURE.md`](./docs/DIRECTORY_STRUCTURE.md): 디렉토리 구조와 각 위치의 책임
- [`docs/ITERATION_FRAMEWORK.md`](./docs/ITERATION_FRAMEWORK.md): 주간/월간/분기별 반복 개선 프로세스

### 문서 디렉토리
- [`docs/design-docs/index.md`](./docs/design-docs/index.md): 기술 설계와 의사결정 근거
- [`docs/product-specs/index.md`](./docs/product-specs/index.md): 사용자 관점 요구사항과 행동 정의
- [`docs/api-spec/README.md`](./docs/api-spec/README.md): 외부 API 통합 명세
- [`docs/domain.md`](./docs/domain.md): 도메인 상태와 정책 기준
- [`docs/domains/README.md`](./docs/domains/README.md): 도메인별 개념과 테스트 보장 범위
- [`docs/exec-plans/active/README.md`](./docs/exec-plans/active/README.md): 진행 중 실행 계획
- [`docs/exec-plans/completed/README.md`](./docs/exec-plans/completed/README.md): 완료된 실행 계획 보관
- [`docs/generated/db-schema.md`](./docs/generated/db-schema.md): 도메인 문서 기반 파생 스키마 스냅샷
- [`docs/generated/test-inventory.md`](./docs/generated/test-inventory.md): 현재 pytest 테스트 파일/함수 파생 인벤토리
- [`docs/references/`](./docs/references/): 외부 도구와 플랫폼 참고 메모

## 문서 책임 규칙

- 제품 동작이 바뀌면 먼저 `docs/product-specs/`를 갱신한다.
- 횡단 관심사나 장기 구조 결정은 `docs/design-docs/`에 남긴다.
- 실행 순서, 검증, 후속 작업은 `docs/exec-plans/`에서 관리한다.
- 구현이나 모델에서 파생된 사실은 `docs/generated/`에 반영한다.
- 도메인별 개념과 테스트가 보장하는 시나리오는 `docs/domains/`에 기록한다.
- 영구 가드레일은 해당 `docs/*.md` 상위 문서에 기록한다.

## 단기 우선순위

- 도메인 모델, API 계약, 생성 스키마를 서로 정렬된 상태로 유지한다.
- 실행 계획을 통해 아이디어를 검증 가능한 작업 단위로 끊는다.
- 코드가 커지기 전에 품질, 신뢰성, 보안 기준을 먼저 명시한다.
