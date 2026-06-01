# OrderRun FastAPI 전환 설계

## 1. 목표

기존 Spring Boot 중심 구조를 FastAPI 기반으로 재설계하되, 도메인 개념은 유지하고 구현 복잡도는 학습 가능한 수준으로 제한한다.

핵심 목표는 다음과 같다.

- 엔티티와 상태 전이를 Python 코드로 명확하게 표현
- OpenAPI와 실제 응답의 불일치 최소화
- MySQL 스키마와 애플리케이션 레이어를 느슨하게 분리
- 테스트 가능하고 확장 가능한 구조 확보

## 2. 아키텍처 스타일

권장 아키텍처는 도메인 중심 `vertical slice` 구조다.

FastAPI에서는 전역 `controllers`, `services`, `repositories`, `schemas` 폴더로 나누는 방식보다 각 도메인 내부에서 HTTP, 유스케이스, 영속성 책임을 함께 배치하는 방식이 유지보수와 학습 측면에서 더 유리하다.

핵심 원칙:

- 도메인별로 `router -> service -> repository -> model` 흐름을 닫는다.
- 공통 인프라는 `core`, `db`, `common`으로만 분리한다.
- ORM 모델과 API 스키마를 분리한다.
- 트랜잭션은 서비스 계층에서 관리한다.
- 학습 프로젝트 범위를 넘는 과도한 패턴 도입은 피한다.

권장 구조:

```text
app/
  main.py
  core/
    settings.py
    security.py
    exceptions.py
    logging.py
  db/
    base.py
    session.py
    models.py
  common/
    response.py
    pagination.py
    enums.py
  user/
    model.py
    schema.py
    repository.py
    service.py
    router.py
  proposal/
    model.py
    schema.py
    repository.py
    service.py
    router.py
    policy.py
  offer/
    model.py
    schema.py
    repository.py
    service.py
    router.py
  mission/
    model.py
    schema.py
    repository.py
    service.py
    router.py
  payment/
    model.py
    schema.py
    repository.py
    service.py
    router.py
tests/
  user/
  proposal/
  offer/
  mission/
  payment/
```

도메인 내부 책임:

| 파일 | 책임 |
| --- | --- |
| `router.py` | `APIRouter` 선언, 요청 파라미터 처리, 인증 의존성 연결, 응답 반환 |
| `schema.py` | Pydantic 요청/응답 DTO |
| `service.py` | 유스케이스, 상태 전이, 권한 검증, 트랜잭션 경계 |
| `repository.py` | SQLAlchemy 조회/저장 |
| `model.py` | DB 매핑 모델 |
| `policy.py` | 상태 전이 규칙, 도메인 정책이 커질 때만 선택적으로 사용 |

도메인 밖 공통 책임:

| 디렉터리 | 책임 |
| --- | --- |
| `core` | 설정, 예외, 보안, 로깅 |
| `db` | SQLAlchemy Base, 엔진, 세션, DB 초기화 |
| `common` | 공통 응답, 페이지네이션, 공용 enum/유틸 |

표준 요청 흐름:

```text
Client
  -> router
  -> service
  -> repository
  -> DB
```

설계 가드레일:

- `router.py`에서 직접 DB 쿼리를 수행하지 않는다.
- `repository.py`에는 비즈니스 규칙을 넣지 않는다.
- `model.py`에는 상태 전이와 권한 검증 로직을 넣지 않는다.
- `service.py`는 FastAPI 객체에 직접 의존하지 않는다.
- API Request/Response DTO는 다른 API DTO를 상속하지 않는다. 각 endpoint의 요청/응답 스키마는 필드를 명시적으로 선언하고, API 계약의 변경 독립성을 중복 제거보다 우선한다.
- 허용되는 상속은 `BaseModel`, `Enum`, `Generic[T]`, `ApiResponse`, `PageResponse`처럼 프레임워크나 공통 envelope 목적의 상속으로 제한한다.
- 동기 `SQLAlchemy Session`을 사용하는 동안 라우터 endpoint는 기본적으로 `def`를 사용한다. `async def`는 async DB/session/client처럼 호출 경로 전체가 비동기 I/O일 때만 도입한다.
- 초기 버전에서는 `async`보다 동기 `SQLAlchemy 2.x` 구성을 우선 권장한다.

비권장 구조 예시:

```text
app/
  routers/
  services/
  repositories/
  schemas/
  models/
```

위 구조는 파일 수가 늘수록 도메인 단위 탐색과 변경 범위 추적이 어려워질 수 있다.

## 3. 기술 선택 기준

### FastAPI

- OpenAPI 자동 생성
- 의존성 주입과 테스트 편의성
- 학습용 프로젝트에 적합한 낮은 진입 장벽

### SQLAlchemy 2.x

- 업계 표준에 가까운 ORM 선택지
- 세션/트랜잭션 제어가 명확함
- 복잡한 관계 매핑과 쿼리 확장에 유리
- 초기 학습 프로젝트에서는 동기 세션 구성이 단순하고 안정적임

### Pydantic 2.x

- 요청/응답 검증
- OpenAPI 스키마 자동화
- DTO 계층을 명시적으로 유지 가능

### Alembic

- 스키마 변경 이력 관리
- MySQL 마이그레이션 표준 도구

## 4. 모델 매핑 전략

| 기존 개념 | FastAPI 모델 | 비고 |
| --- | --- | --- |
| `User` | `user/model.py::User` | 계정과 프로필을 우선 통합 |
| `Proposal` | `proposal/model.py::Proposal` | 예산, 카테고리, 마감시각 포함 |
| `Offer` | `offer/model.py::Offer` | Proposal에 종속 |
| `Mission` | `mission/model.py::Mission` | Offer 수락 후 생성 |
| `Payment` | `payment/model.py::Payment` | Mission과 1:1 |
| `Terms` | `user/model.py::TermsAgreement` 또는 별도 도메인 | 초기엔 선택 구현 가능 |

권장 원칙:

1. DB 모델과 API 스키마를 분리한다.
2. ORM 모델에 비즈니스 로직을 과도하게 넣지 않는다.
3. 상태 전이는 서비스 계층 또는 도메인 정책 객체에서 수행한다.
4. 리포지토리는 도메인별로 얇게 유지하고, 조회와 저장 책임에 집중한다.

## 5. 디렉터리 예시

```text
app/
  main.py
  core/settings.py
  core/security.py
  core/exceptions.py
  core/logging.py
  db/base.py
  db/session.py
  db/models.py
  common/response.py
  common/pagination.py
  common/enums.py
  user/model.py
  user/schema.py
  user/repository.py
  user/service.py
  user/router.py
  proposal/model.py
  proposal/schema.py
  proposal/repository.py
  proposal/service.py
  proposal/router.py
  proposal/policy.py
  offer/model.py
  offer/schema.py
  offer/repository.py
  offer/service.py
  offer/router.py
  mission/model.py
  mission/schema.py
  mission/repository.py
  mission/service.py
  mission/router.py
  payment/model.py
  payment/schema.py
  payment/repository.py
  payment/service.py
  payment/router.py
tests/
  user/
  proposal/
  offer/
  mission/
  payment/
```

`main.py` 책임:

- FastAPI 앱 생성
- 미들웨어 등록
- 예외 핸들러 등록
- 도메인 라우터 포함

`main.py` 비권장 책임:

- 비즈니스 로직 처리
- 직접 DB 접근
- 개별 도메인 정책 구현

## 6. 데이터베이스 설계 원칙

### 기본 원칙

- 모든 PK는 `BIGINT AUTO_INCREMENT` 또는 `UUID` 중 하나로 통일한다.
- MVP 기준으로는 `BIGINT`가 학습 부담이 낮다.
- FK에는 필요한 인덱스를 추가한다.
- 금액은 `DECIMAL` 사용, 시간은 UTC 저장을 기본으로 한다.

### 권장 인덱스

| 테이블 | 인덱스 |
| --- | --- |
| `users` | `uk_users_email`, `uk_users_nickname` |
| `proposals` | `idx_proposals_customer_id`, `idx_proposals_status` |
| `offers` | `idx_offers_proposal_id`, `idx_offers_runner_id`, `uk_offers_proposal_runner` |
| `missions` | `idx_missions_runner_id`, `idx_missions_customer_id`, `uk_missions_offer_id` |
| `payments` | `uk_payments_mission_id`, `idx_payments_status` |

## 7. 트랜잭션 전략

다음 유스케이스는 단일 트랜잭션으로 묶는다.

- Offer 수락 + Proposal 상태 변경 + Mission 생성
- Mission 완료 + Payment 확정
- Mission 취소 + Payment 취소 또는 환불

서비스 계층에서 세션 단위 트랜잭션을 관리한다.

## 8. 예외 처리 전략

`core/exceptions.py`에 도메인 예외를 정의한다.

예시:

- `NotFoundException`
- `ForbiddenException`
- `ValidationException`
- `InvalidStateTransitionException`
- `ExternalProviderException`

각 예외는 공통 에러 응답 포맷으로 매핑한다.

## 9. 인증/인가 설계

초기 단계:

- JWT access token 단일 사용
- 로그인은 단순 이메일 기반 mock 또는 테스트용 토큰 발급

확장 단계:

- refresh token 도입
- 소셜 로그인 연동
- 관리자 역할 분리

인가 원칙:

- 리소스 소유자 검증
- 역할 기반 접근 제어
- 관리자 override 정책

## 10. 테스트 전략

### 단위 테스트

- 상태 전이 함수
- 권한 검증 함수
- 서비스 계층 정책 로직

### 통합 테스트

- FastAPI router + service + DB 통합
- TestClient 또는 httpx AsyncClient 사용
- 각 엔드포인트의 정상/예외 케이스 검증

### 계약 테스트

- OpenAPI 스키마와 실제 응답 필드 비교
- 실패했던 Spring 문서 테스트 이력을 고려해 응답 필드 누락을 집중 검증

## 11. 전환 단계

### Phase 1. 기반 구축

- FastAPI 프로젝트 초기화
- 설정, DB 세션, 공통 예외, 공통 응답 구현
- Alembic 초기 세팅

### Phase 2. User 컨텍스트

- User 모델과 사용자 조회/수정 API 구현
- JWT 테스트 토큰 기능 추가

### Phase 3. Bidding 컨텍스트

- Proposal 생성/조회/수정
- Offer 생성/조회/수락

### Phase 4. Execution 컨텍스트

- Mission 생성, 조회, 시작, 완료
- 상태 전이 테스트 보강

### Phase 5. Settlement 컨텍스트

- Payment 조회, 확정, 환불 인터페이스
- 외부 PG는 mock adapter로 연결

### Phase 6. 안정화

- 문서 정리
- 회귀 테스트 추가
- 권한, 에러 코드, 감사 로그 점검

## 12. 운영 관점 권장 사항

학습용 프로젝트라도 아래는 포함하는 것이 좋다.

- 요청 단위 `request_id` 로깅
- 구조화 로그
- 환경별 설정 분리
- `.env` 기반 비밀정보 관리
- 헬스체크 엔드포인트

## 13. 초기 구현 체크리스트

- [ ] FastAPI 앱 부트스트랩
- [ ] SQLAlchemy Base / Session 설정
- [ ] Alembic 초기 리비전
- [ ] User, Proposal, Offer, Mission, Payment 모델 생성
- [ ] 공통 에러 응답 구현
- [ ] 인증 의존성 구현
- [ ] Proposal API 구현
- [ ] Offer 수락 시 Mission 생성 트랜잭션 구현
- [ ] Mission 완료 시 Payment 확정 정책 구현
- [ ] pytest 통합 테스트 작성

## 14. 결정 로그

| 항목 | 결정 |
| --- | --- |
| 웹 프레임워크 | FastAPI |
| ORM | SQLAlchemy 2.x |
| DB 접근 방식 | 동기 세션 우선 |
| 검증/스키마 | Pydantic 2.x |
| DB | MySQL |
| 마이그레이션 | Alembic |
| 인증 | JWT Bearer |
| 패키지 구조 | 도메인 중심 vertical slice |
| API 스타일 | REST + 일부 action endpoint |
| 트랜잭션 기준 | 서비스 계층 |
