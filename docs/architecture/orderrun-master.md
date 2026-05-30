# OrderRun 통합 설계 마스터

## 1. 문서 목적

이 문서는 `OrderRun` 백엔드를 `Python + FastAPI + MySQL` 기반으로 설계하고 구현하기 위한 기준 문서다. 학습용 프로젝트이지만, 실제 실무 문서처럼 범위, 도메인, API 계약, 데이터 모델, 전환 순서를 분리해 관리한다.

본 문서는 아래 두 관점을 함께 다룬다.

- `As-Is`: 기존 Spring Boot 기반 구현 및 분석 결과 기준의 현행 상태
- `To-Be`: FastAPI 기반 목표 설계

## 2. 전제와 근거

현재 저장소에는 구현 코드가 없으므로 `As-Is` 정보는 사용자가 제공한 기존 분석 로그를 기준으로 정리했다.

- 기존 구현 기술: Java, Spring Boot, Gradle
- 확인된 핵심 엔티티: `User`, `Proposal`, `Offer`, `Mission`, `Payment`
- 확인된 핵심 API 영역: `User`, `Proposal`, `Offer`, `Mission`
- 확인된 미완료 영역: 인증 연동, 약관 처리, 정산 트리거, 권한 체크, 알림 설정, 운영자 분쟁 처리
- 기존 테스트 상태: 총 `31`건 중 `29`건 통과, `ProposalControllerDocsTest` 계열 `2`건 실패

따라서 이 문서는 현행 구현 사실과 목표 설계를 혼합하지 않고 구분해서 기록한다.

## 3. 프로젝트 개요

`OrderRun`은 사용자가 요청서를 등록하고, 수행자가 제안을 보내며, 요청자가 제안을 수락한 뒤 작업이 수행되고 정산되는 구조의 매칭 플랫폼으로 가정한다.

핵심 흐름은 다음과 같다.

1. 사용자가 요청서(`Proposal`)를 생성한다.
2. 수행자가 제안(`Offer`)을 등록한다.
3. 요청자가 특정 제안을 수락한다.
4. 실제 수행 단위인 미션(`Mission`)이 생성되고 상태가 진행된다.
5. 완료 이후 결제/정산(`Payment`)이 처리된다.

## 4. 범위

### 포함 범위

- 도메인 모델 정의
- 엔티티 및 상태 전이 정의
- REST API 계약 정의
- FastAPI 애플리케이션 구조 설계
- MySQL 스키마 설계 방향
- 테스트 전략과 전환 로드맵

### 제외 범위

- 프론트엔드 설계
- 인프라 상세 구현
- 외부 PG사 세부 연동 명세
- 운영 조직용 백오피스 상세 화면 설계

## 5. 목표 기술 스택

| 구분 | 선택 |
| --- | --- |
| Language | Python 3.12 |
| Web Framework | FastAPI |
| ORM | SQLAlchemy 2.x |
| Schema Validation | Pydantic 2.x |
| Database | MySQL 8.x |
| Migration | Alembic |
| Test | pytest, httpx, FastAPI TestClient |
| Auth | JWT Bearer |
| Packaging | Poetry 또는 uv |

## 6. 컨텍스트 분해

`OrderRun`은 아래 4개 bounded context로 나눈다.

| Context | 책임 | 핵심 엔티티 |
| --- | --- | --- |
| User | 사용자 계정, 프로필, 권한, 약관 동의 | `User`, `UserProfile`, `TermsAgreement` |
| Bidding | 요청 등록과 제안 경쟁 | `Proposal`, `Offer` |
| Execution | 수락 이후 작업 수행 | `Mission` |
| Settlement | 결제, 환불, 정산 | `Payment`, `SettlementRecord` |

## 7. 현행 구현 상태 요약

| 항목 | 상태 | 비고 |
| --- | --- | --- |
| User 엔티티 | 구현됨 | 핵심 사용자 정보 존재 |
| Proposal 엔티티 | 구현됨 | 요청 등록 중심 |
| Offer 엔티티 | 구현됨 | Proposal 대상 제안 |
| Mission 엔티티 | 구현됨 | 수락 후 수행 단위 |
| Payment 엔티티 | 구현됨 | 존재는 확인되나 연계 흐름은 제한적 |
| User API | 일부 구현 | 인증/권한은 미완료 |
| Proposal API | 일부 구현 | 문서 테스트와 응답 스펙 일부 불일치 |
| Offer API | 일부 구현 | 제안 생성 및 조회 중심으로 추정 |
| Mission API | 일부 구현 | 상태 변경 로직 일부 존재 |
| Terms API | 설계만 존재 | 실구현 미확인 |
| Auth 연동 | 미완료 | 임시 사용자 식별 흐름 존재 가능 |
| Payment 정산 자동화 | 미완료 | 후속 과제로 남음 |

## 8. 목표 품질 기준

### 기능 품질

- 요청 등록, 제안, 수락, 수행, 정산 흐름이 끊기지 않아야 한다.
- 모든 상태 전이는 명시된 규칙에 따라 검증되어야 한다.
- 권한이 없는 사용자는 타인의 리소스를 수정할 수 없어야 한다.

### 비기능 품질

- API 응답 시간 목표: 일반 조회 `p95 300ms` 이하
- 데이터 일관성: 상태 전이와 결제 변경은 트랜잭션으로 보호
- 문서 일치성: OpenAPI와 실제 응답 모델이 불일치하지 않아야 함
- 테스트 기준: 단위 테스트, API 통합 테스트, 상태 전이 테스트 포함

## 9. 문서 구성

- [도메인 모델](./orderrun-domain-model.md)
- [API 계약](../api-spec/README.md)
- [도메인 정책](../domain.md)
- [FastAPI 전환 설계](./orderrun-fastapi-transition.md)

## 10. 핵심 설계 원칙

1. 현행 도메인 이름을 최대한 유지하되, 패키지 구조는 도메인 중심 `vertical slice`로 재정리한다.
2. 각 도메인은 기본적으로 `router -> service -> repository -> model` 흐름을 따른다.
3. `core`, `db`, `common`만 도메인 밖 공통 인프라로 분리한다.
4. 상태 전이와 권한 검증은 서비스 계층에 집중시킨다.
5. 응답 계약은 OpenAPI와 Pydantic 모델에서 단일 출처로 관리한다.
6. 학습용 프로젝트라도 결제, 권한, 에러 모델은 임시 구현으로 흐리지 않는다.
7. 학습 프로젝트 범위를 넘는 CQRS, 이벤트 버스, 과도한 추상화는 초기 버전에서 도입하지 않는다.

## 11. 리스크와 미확정 사항

| 항목 | 상태 | 대응 |
| --- | --- | --- |
| 현행 Spring 세부 필드 정의 미확인 | 높음 | 구현 시작 전 실제 엔티티 필드와 이 문서 비교 필요 |
| 인증 방식 세부 확정 미완료 | 중간 | 초기 버전은 JWT 자체 발급 기준으로 시작 |
| PG 연동 방식 미정 | 중간 | 인터페이스만 정의하고 Stub으로 개발 |
| 운영자 분쟁 처리 범위 미정 | 중간 | MVP 범위에서는 보류 |

## 12. 권장 구현 순서

1. User, Proposal, Offer, Mission, Payment 스키마를 확정한다.
2. User/Auth 최소 기능을 먼저 만든다.
3. Proposal 생성/조회 API를 구현한다.
4. Offer 생성/조회/수락 흐름을 구현한다.
5. Mission 상태 전이를 구현한다.
6. Payment 예약/확정/환불 인터페이스를 구현한다.
7. 테스트와 OpenAPI 문서를 맞춘다.

## 13. 완료 기준

- 핵심 컨텍스트별 엔티티와 상태 전이가 문서화되어 있다.
- 주요 REST API가 요청/응답 스키마와 함께 정의되어 있다.
- FastAPI 패키지 구조와 구현 규칙이 정리되어 있다.
- 전환 순서와 테스트 전략이 구현 가능한 수준으로 명시되어 있다.
