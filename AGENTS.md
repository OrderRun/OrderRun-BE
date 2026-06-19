# OrderRun-BE 작업 가이드

## 목적

이 저장소는 문서를 중심으로 설계, 계획, 구현 방향을 관리하는 엔지니어링 하네스를 사용한다.
코드 작업이 커지기 전에 관련 문서 위치와 기준 문서를 먼저 확인한다.

## 운영 원칙

- 다음 단계가 저위험이고 되돌릴 수 있다면 직접 진행한다.
- 변경은 작고 검토 가능하게 유지하고, 가능한 한 문서나 계획에 연결한다.
- 추정보다 근거를 우선한다. 결정이 바뀌면 관련 기준 문서를 함께 갱신한다.
- 새 추상화를 만들기 전에 기존 패턴과 구조를 재사용한다.
- 완료 주장은 변경 크기에 맞는 최소 검증 근거와 함께 한다.

## 기준 문서 맵

### 하네스 엔지니어링 핵심
- [`docs/HARNESS_ENGINEERING.md`](./docs/HARNESS_ENGINEERING.md): 문서 중심 개발 방법론
- [`docs/DIRECTORY_STRUCTURE.md`](./docs/DIRECTORY_STRUCTURE.md): 디렉토리 구조와 책임
- [`docs/ITERATION_FRAMEWORK.md`](./docs/ITERATION_FRAMEWORK.md): 반복 개선 프레임워크

### 시스템과 작업 규칙
- [`ARCHITECTURE.md`](./ARCHITECTURE.md): 시스템 개요와 문서 진입점
- [`docs/DESIGN.md`](./docs/DESIGN.md): 설계 문서 작성 규칙
- [`docs/PLANS.md`](./docs/PLANS.md): 실행 계획 운영 방식
- [`docs/PRODUCT_SENSE.md`](./docs/PRODUCT_SENSE.md): 제품 우선순위 판단 기준
- [`docs/QUALITY_SCORE.md`](./docs/QUALITY_SCORE.md): 품질 평가 기준
- [`docs/references/testing-guidelines.md`](./docs/references/testing-guidelines.md): 테스트 작성 기준
- [`docs/RELIABILITY.md`](./docs/RELIABILITY.md): 신뢰성 기준
- [`docs/SECURITY.md`](./docs/SECURITY.md): 보안 기준

## 작업 규칙

- 새 기능 작업은 가능하면 `docs/product-specs/`의 명시적 스펙과 연결한다.
- 구조적이거나 장기 영향이 큰 결정은 `docs/design-docs/`에 남긴다.
- 진행 중 작업은 `docs/exec-plans/active/`, 완료된 작업은 `docs/exec-plans/completed/`로 관리한다.
- 코드나 설계로부터 파생된 산출물은 `docs/generated/`에 둔다.
- 외부 도구, 플랫폼, 참고 자료 메모는 `docs/references/`에 둔다.

## 마이그레이션 규칙

- Alembic revision ID는 현재 저장소처럼 설명형 이름을 사용할 수 있다.
- fresh MySQL DB의 `alembic_version.version_num`은 `varchar(255)`로 생성되도록 `alembic/env.py`에서 보장한다.
- 로컬 fresh MySQL DB도 `alembic upgrade head`로 초기 세팅 가능해야 한다.
- 현재 모델 기준 baseline 이후에 컬럼/인덱스를 추가하는 migration은 이미 존재할 때 실패하지 않도록 작성한다.
- 기존 DB의 `alembic_version` 테이블은 자동 변경하지 않는다.

## 테스트 실행 규칙

- 통합 테스트를 실행할 때는 `docker-compose.test.yml`의 `mysql-test` 서비스를 사용한다.
- 테스트 DB는 `docker compose -f docker-compose.test.yml up -d mysql-test`로 띄우고, `orderrun-mysql-test`가 `healthy`인지 확인한 뒤 `pytest`를 실행한다.
- 테스트 실행 env는 compose 설정과 맞춘다: `DB_HOST=127.0.0.1`, `DB_PORT=3307`, `DB_USERNAME=orderrun_user`, `DB_PASSWORD=orderrun_pass`, `DB_NAME=orderrun`.
- 통합 테스트 실패를 로컬 MySQL 인증/스키마 문제로 판단하기 전에 위 테스트 compose 환경으로 재실행한다.

## 완료 전 확인

1. 관련 문서 엔트리가 존재하거나 갱신되었는지 확인한다.
2. 상위 문서 간 링크가 깨지지 않았는지 확인한다.
3. 남은 리스크와 후속 작업이 계획 또는 트래커에 기록되었는지 확인한다.
