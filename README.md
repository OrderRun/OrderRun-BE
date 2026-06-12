# OrderRun-BE

`OrderRun` 백엔드의 FastAPI 전환과 구현을 위한 문서 중심 저장소다.

## 시작점

- [Agent Guide](./AGENTS.md)
- [Architecture](./ARCHITECTURE.md)

## 문서 허브

### 하네스 엔지니어링 가이드
- [Harness Engineering](./docs/HARNESS_ENGINEERING.md) - 문서 중심 개발 방법론
- [Directory Structure](./docs/DIRECTORY_STRUCTURE.md) - 디렉토리 구조와 책임
- [Iteration Framework](./docs/ITERATION_FRAMEWORK.md) - 반복 개선 프레임워크

### 작업 가이드
- [Design Guide](./docs/DESIGN.md)
- [Planning Guide](./docs/PLANS.md)
- [Product Sense](./docs/PRODUCT_SENSE.md)
- [Quality Score](./docs/QUALITY_SCORE.md)
- [Reliability Guide](./docs/RELIABILITY.md)
- [Security Guide](./docs/SECURITY.md)

## 핵심 문서 트리

- [Design Docs Index](./docs/design-docs/index.md)
- [Product Specs Index](./docs/product-specs/index.md)
- [API Spec](./docs/api-spec/README.md)
- [Domain Policy](./docs/domain.md)
- [Tech Debt Tracker](./docs/exec-plans/tech-debt-tracker.md)
- [EC2 Staging/Production Deployment Plan](./docs/exec-plans/active/2026-06-12-ec2-prod-staging-split.md)
- [Generated DB Schema](./docs/generated/db-schema.md)
- [로컬 개발 환경 세팅](./docs/setup/local-development.md)

## 기본 전제

- Language: Python
- Framework: FastAPI
- Database: MySQL
- ORM: SQLAlchemy 2.x
- Schema Validation: Pydantic 2.x
- Runtime: Docker Compose on EC2
- Edge Proxy: Nginx
- Staging URL: `http://43.200.56.9`, `http://staging-api.kkobung-dan.store`
- Production URL: `api.kkobung-dan.store` (준비 중)
