# 디렉토리 구조 가이드

## 목적

이 문서는 하네스 엔지니어링을 위한 최적 디렉토리 구조와 각 디렉토리의 책임을 정의한다.

## 루트 레벨 구조

```
OrderRun-BE/
├── README.md                    # 프로젝트 개요, 빠른 시작
├── AGENTS.md                    # AI Agent 작업 규칙
├── ARCHITECTURE.md              # 시스템 지도, 문서 진입점
├── .gitignore
├── pyproject.toml               # Python 의존성, 도구 설정
├── app/                         # 애플리케이션 코드
└── docs/                        # 모든 문서 하네스
```

## docs/ 하위 구조

### 상위 가이드 문서

```
docs/
├── HARNESS_ENGINEERING.md       # 하네스 방법론 (본질)
├── DESIGN.md                    # 설계 문서 작성 규칙
├── PLANS.md                     # 계획 문서 운영 방식
├── PRODUCT_SENSE.md             # 제품 우선순위 판단
├── QUALITY_SCORE.md             # 품질 평가 기준
├── RELIABILITY.md               # 신뢰성 기준
├── SECURITY.md                  # 보안 기준
├── domain.md                    # 도메인 상태와 정책 정본
└── DIRECTORY_STRUCTURE.md       # 본 문서
```

**책임:**
- 각 문서 유형의 작성 규칙 정의
- 품질, 보안, 신뢰성 가드레일 명시
- 모든 참여자 (AI/인간)가 따라야 할 원칙 제시

### 설계 문서 (design-docs/)

```
docs/design-docs/
├── index.md                     # 설계 문서 카탈로그
├── core-beliefs.md              # 핵심 설계 철학
├── api-versioning.md            # API 버전 관리 전략
├── error-handling.md            # 에러 처리 패턴
├── domain-boundaries.md         # 도메인 경계 정의
└── ...
```

**용도:**
- 구조, 경계, 패턴에 영향을 주는 기술 결정
- 여러 모듈에 걸친 재사용 가능한 구현 패턴
- 유지보수 비용에 영향을 주는 장기 아키텍처

**작성 시점:**
- 도메인 경계 변경
- API 형태와 호환성 규칙 결정
- 영속성 모델과 마이그레이션 방향 설정
- 신뢰성 또는 보안 구조 변경

**금지:**
- 일회성 진행 상황 기록
- 특정 작업의 단계별 실행 계획
- 제품 기능 스펙

### 제품 스펙 (product-specs/)

```
docs/product-specs/
├── index.md                     # 제품 스펙 카탈로그
├── new-user-onboarding.md       # 신규 사용자 온보딩
├── proposal-lifecycle.md        # 요청 생명주기
├── offer-bidding.md             # 제안 입찰 프로세스
├── payment-flow.md              # 결제 플로우
└── ...
```

**용도:**
- 사용자 관점 요구사항과 행동 정의
- 제품 기능의 입력, 출력, 상태 전이
- 비즈니스 규칙과 제약 조건

**작성 시점:**
- 새 기능 추가
- 기존 기능의 동작 변경
- 사용자 플로우 수정

**금지:**
- 구현 세부사항 (어떤 라이브러리, 어떤 알고리즘)
- 데이터베이스 스키마
- API 엔드포인트 경로

### 실행 계획 (exec-plans/)

```
docs/exec-plans/
├── active/
│   ├── README.md                # 진행 중 계획 목록
│   ├── 2026-03-20-api-auth.md
│   └── 2026-03-24-payment-integration.md
├── completed/
│   ├── README.md                # 완료된 계획 보관
│   └── 2026-03-15-db-migration.md
└── tech-debt-tracker.md         # 장기 부채 항목
```

**용도:**
- 작업 분해와 순서 정의
- 검증 전략과 롤백 계획
- 리스크와 가정 명시

**작성 시점:**
- 3단계 이상의 복잡한 작업 착수 전
- 여러 모듈에 걸친 변경 시작 전
- 불확실성이 높은 작업 계획 시

**파일명 규칙:**
- `YYYY-MM-DD-short-title.md`
- 시간순 정렬 가능
- 추적과 참조 용이

**수명 주기:**
1. `active/`에서 계획 작성
2. 작업 진행하며 계획 갱신
3. 완료 후 `completed/`로 이동
4. 남은 부채는 `tech-debt-tracker.md`에 기록

### 도메인 문서 (domains/)

```
docs/domains/
├── README.md                    # 도메인별 문서 카탈로그
├── proposal/
│   ├── README.md                # 도메인 개념과 책임
│   └── test-scenarios.md        # 테스트가 보장하는 시나리오
├── offer/
│   ├── README.md
│   └── test-scenarios.md
└── ...
```

**용도:**
- 도메인별 개념, 책임, 주요 정책 해석
- 각 도메인 테스트가 보장하는 정상/실패/계약 시나리오
- `api-spec/README.md`, `domain.md`, 실제 테스트 사이의 사람이 읽는 연결 문서

**금지:**
- API 필드와 상태 enum의 정본화 (→ `api-spec/README.md`, `domain.md`)
- 테스트 파일 목록과 함수 수의 중복 수기 관리

### 생성 문서 (generated/)

```
docs/generated/
└── db-schema.md                 # 데이터베이스 스키마 스냅샷
```

**용도:**
- 코드, 모델, 설계 정본에서 파생된 고가치 스냅샷
- 리뷰 시 현재 구조를 빠르게 확인하기 위한 표 형식 산출물

**생성 시점:**
- 모델 변경 후
- 영속성 설계 변경 후
- 스키마 리뷰 전

**주의:**
- 정본은 `design-docs/`, `domain.md`, `api-spec/`, `domains/`다.
- `generated/` 문서는 정본이 아니라 파생 스냅샷이다.
- 새 generated 문서는 재생성 절차가 명확할 때만 추가한다.
- 테스트 보장 시나리오는 `domains/`에 두고, 테스트 파일/함수 수는 명령으로 확인한다.

### 참고 자료 (references/)

```
docs/references/
├── fastapi-best-practices.md
├── sqlalchemy-patterns.md
├── mysql-performance.md
├── payment-gateway-api.md
└── ...
```

**용도:**
- 외부 도구, 플랫폼, 라이브러리 메모
- 공식 문서 링크와 핵심 발췌
- 의사결정 시 참고한 자료

**금지:**
- 프로젝트 고유 설계 결정 (→ design-docs/)
- 실행 계획 (→ exec-plans/)

### API 명세 (api-spec/)

```
docs/api-spec/
├── README.md                    # 외부 API 요청/응답 계약 정본
└── implementation-gaps.md       # 정본과 현재 구현 사이의 갭 추적
```

**용도:**
- 외부 클라이언트가 따를 HTTP 요청/응답 계약
- 공통 응답 래퍼, 에러 형식, 인증 예외, 페이징 규칙
- API 정본과 구현 사이의 차이 추적

### 셋업 가이드 (setup/)

```
docs/setup/
├── local-development.md         # 로컬 개발 환경
├── docker-compose.md            # 컨테이너 구성
├── ci-cd.md                     # CI/CD 파이프라인
└── ...
```

**용도:**
- 환경 구성 단계
- 도구 설치 가이드
- 트러블슈팅

### 학습 자료 (study/)

```
docs/study/
├── python-basics-from-main-py.md
└── ...
```

**용도:**
- 학습 메모
- 실험 결과
- 프로토타입 기록

**주의:**
- 공식 문서가 아님
- 개인 또는 팀 학습용
- API 계약, 상태 정책, 설계 결정의 정본으로 참조하지 않음

## app/ 코드 구조

### 권장 레이아웃

```
app/
├── __init__.py
├── main.py                      # FastAPI 앱 진입점
├── core/
│   ├── __init__.py
│   ├── config.py                # 설정
│   ├── deps.py                  # 의존성 주입
│   └── security.py              # 인증/인가
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── proposal.py
│   └── ...                      # SQLAlchemy 모델
├── schemas/
│   ├── __init__.py
│   ├── user.py
│   └── ...                      # Pydantic 스키마
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── router.py            # v1 하위 라우터 조립
│   │   ├── user_auth/
│   │   │   ├── auth_router.py
│   │   │   └── user_router.py
│   │   ├── proposal/
│   │   │   └── proposal_router.py
│   │   └── ...                  # 도메인별 API 패키지
│   └── deps.py                  # API 의존성
├── services/
│   ├── __init__.py
│   ├── user_service.py
│   └── ...                      # 비즈니스 로직
├── repositories/
│   ├── __init__.py
│   ├── user_repository.py
│   └── ...                      # 데이터 액세스
└── utils/
    ├── __init__.py
    └── ...                      # 유틸리티
```

### 디렉토리 책임

| 디렉토리 | 책임 | 의존성 방향 |
|---------|-----|-----------|
| `core/` | 앱 전역 설정, 의존성, 보안 | 없음 |
| `models/` | SQLAlchemy ORM 모델 | core |
| `schemas/` | Pydantic 요청/응답 스키마 | models |
| `repositories/` | 데이터 액세스 레이어 | models |
| `services/` | 비즈니스 로직 | repositories, schemas |
| `api/` | 도메인별 FastAPI 라우터와 버전별 조립 | services, schemas |
| `utils/` | 순수 유틸리티 함수 | 없음 |

**의존성 흐름:**
```
api → services → repositories → models
  ↓       ↓           ↓           ↓
schemas ←────────────────────────┘
```

## 파일 배치 결정 트리

### 새 파일을 어디에 둘까?

```
Q: 이것은 코드인가, 문서인가?
├─ 코드 → app/
│   Q: 어떤 계층인가?
│   ├─ 데이터 모델 → app/models/
│   ├─ API 계약 → app/schemas/
│   ├─ 비즈니스 로직 → app/services/
│   ├─ 데이터 액세스 → app/repositories/
│   └─ API 엔드포인트 → app/api/v1/<domain>/*_router.py
│
└─ 문서 → docs/
    Q: 어떤 종류의 문서인가?
    ├─ 기술 결정과 아키텍처 → docs/design-docs/
    ├─ 제품 기능 스펙 → docs/product-specs/
    ├─ 실행 계획 → docs/exec-plans/active/
    ├─ 코드에서 파생 → docs/generated/
    ├─ 외부 참고 자료 → docs/references/
    └─ 환경 설정 → docs/setup/
```

## 문서 연결 규칙

### 링크 방향

**위에서 아래로 (권장):**
```
ARCHITECTURE.md
    ↓
docs/design-docs/index.md
    ↓
docs/design-docs/core-beliefs.md
```

**아래에서 위로 (제한적):**
- 실행 계획 → 설계 문서 (근거 참조)
- 설계 문서 → 제품 스펙 (요구사항 참조)

**금지:**
- 순환 참조
- 동일 레벨 간 과도한 교차 참조

### 링크 형식

**상대 경로 사용:**
```markdown
[ARCHITECTURE](../ARCHITECTURE.md)
[Design Docs](./design-docs/index.md)
```

**앵커 링크 사용:**
```markdown
[Core Beliefs](./design-docs/core-beliefs.md)
```

## 파일명 규칙

### 문서

- **가이드 문서:** `UPPERCASE.md` (예: `DESIGN.md`, `SECURITY.md`)
- **설계/스펙 문서:** `lowercase-kebab-case.md` (예: `api-versioning.md`)
- **실행 계획:** `YYYY-MM-DD-short-title.md` (예: `2026-03-20-api-auth.md`)
- **인덱스:** `index.md` 또는 `README.md`

### 코드

- **Python 모듈:** `lowercase_snake_case.py` (예: `user_service.py`)
- **설정 파일:** `lowercase-kebab-case` (예: `pyproject.toml`, `docker-compose.yml`)

## 확장 가이드라인

### 새 도메인 추가 시

1. `docs/design-docs/`에 도메인 경계 문서 작성
2. 사용자 행동이 바뀌면 `docs/product-specs/`에 제품 스펙 작성
3. `docs/domains/`에 도메인 개념과 테스트 보장 문서 작성
4. `docs/exec-plans/active/`에 구현 계획 작성
5. `app/models/`에 모델 추가
6. `app/schemas/`, `app/services/`, `app/repositories/` 순서로 레이어 구현
7. `app/api/v1/<domain>/*_router.py`에 엔드포인트를 추가하고 `app/api/v1/router.py`에 등록
8. 영속성 구조가 바뀌면 `docs/generated/db-schema.md` 갱신

### 새 문서 유형 추가 시

1. `docs/` 아래에 새 디렉토리 생성
2. `docs/NEW_TYPE.md`에 작성 규칙 정의
3. `ARCHITECTURE.md`에 새 유형 책임 명시
4. `docs/DIRECTORY_STRUCTURE.md` (본 문서) 갱신

## 점검 체크리스트

### 주간 점검

- [ ] `exec-plans/active/`에 방치된 계획이 있는가?
- [ ] 완료된 계획이 `completed/`로 이동되었는가?
- [ ] 새로운 코드가 문서와 연결되어 있는가?

### 월간 점검

- [ ] `design-docs/index.md`가 최신 상태인가?
- [ ] `product-specs/index.md`가 최신 상태인가?
- [ ] `generated/` 문서가 코드와 동기화되어 있는가?
- [ ] 링크 무결성 검사 (깨진 링크 없음)

### 분기별 점검

- [ ] 레거시 설계 문서를 `design-docs/`, `domains/`, `product-specs/` 중 알맞은 위치로 정리할 수 있는가?
- [ ] 중복된 설계 문서를 통합할 수 있는가?
- [ ] `references/`의 외부 링크가 유효한가?
- [ ] 디렉토리 구조 개선 기회가 있는가?

## 참고 자료

- [HARNESS_ENGINEERING.md](./HARNESS_ENGINEERING.md) - 하네스 방법론
- [ARCHITECTURE.md](../ARCHITECTURE.md) - 시스템 지도
- [DESIGN.md](./DESIGN.md) - 설계 문서 가이드
- [PLANS.md](./PLANS.md) - 계획 문서 가이드

## 버전 이력

- 2026-03-25: 초안 작성
