# 테스트 작성 가이드

## 목적

OrderRun-BE의 테스트는 API 계약, 상태 전이, DB 저장 결과를 신뢰성 있게 검증하는 것을 우선한다.
새 기능은 기본적으로 통합 테스트로 검증하고, 순수 로직과 외부 연동 포맷은 단위 테스트로 보강한다.

## 테스트 종류

### API 통합 테스트

- FastAPI `TestClient`, MySQL test DB, 공통 fixture를 사용한다.
- HTTP 요청부터 라우터, 서비스, DB 저장/조회, 응답 계약까지 함께 검증한다.
- 상태 전이, 인증/인가, 트랜잭션성 동작, API 응답 필드 변경은 통합 테스트를 기본으로 작성한다.
- 파일명은 `tests/test_{domain}_integration.py`를 사용한다.

### 계약 테스트

- OpenAPI schema, 예시 응답, 공통 error wrapper, response shape를 검증한다.
- API 응답 필드나 status code가 바뀌면 OpenAPI 예시와 계약 테스트를 함께 갱신한다.
- 대표 파일은 `tests/test_openapi.py`다.

### 단위 테스트

- DB와 API 서버 없이 좁은 동작을 검증한다.
- 전화번호 정규화, 시간 변환, 금액 계산, 계좌 masking, provider 요청 payload 구성, error/config 유틸처럼 입출력이 작은 로직에 사용한다.
- 파일명은 `tests/test_{module}.py` 또는 `tests/test_{service}.py`를 사용한다.

## 이름 규칙

- 테스트 함수명은 `test_{행위}_{조건}_{기대결과}` 형식으로 작성한다.
- 예: `test_create_offer_with_valid_proposal_marks_proposal_offered`
- 조건이나 기대결과가 너무 많아 함수명이 길어지면 테스트를 나눈다.
- 한 테스트는 하나의 사용자 행위 또는 하나의 정책 묶음을 검증한다.

## 테스트 데이터

- DB row 생성은 `tests/factories.py`의 `TestDataFactory`를 우선 사용한다.
- API request body는 테스트 파일 안에 `{domain}_payload(**overrides)` helper를 두고 생성한다.
- 모델 직접 생성은 factory가 없거나 관계와 상태를 테스트 안에서 명시하는 편이 더 읽기 쉬울 때만 사용한다.
- `phone`, token, title 식별자처럼 unique 충돌 가능성이 있는 값은 테스트 안에서 명시적으로 다르게 둔다.
- 시간 값은 테스트 목적이 시간 자체가 아니면 helper나 factory 기본값을 사용한다.

## 검증 규칙

- 성공 API는 `status_code`, `message`, 핵심 `data` 필드를 검증한다.
- 응답 필드 계약이 중요하면 `set(body["data"]) == {...}` 또는 전체 dict 비교로 shape를 고정한다.
- 실패 API는 `status_code`와 `error.code`를 반드시 검증한다.
- 상태 전이 API는 응답뿐 아니라 `db.refresh(...)` 후 DB 모델 상태도 검증한다.
- 목록, 정렬, 필터는 id list 또는 id set으로 검증한다.
- 없어야 하는 필드는 `"field" not in data`로 회귀를 막는다.
- 예외 검증은 `pytest.raises`를 기본으로 한다.

## 작성 흐름

1. API 기능 변경이면 먼저 어떤 endpoint와 상태 전이가 바뀌는지 정한다.
2. 기존 도메인 통합 테스트 파일을 찾아 같은 fixture, factory, payload helper 패턴을 따른다.
3. 성공 경로, 대표 실패 경로, DB 상태 변경, 응답 계약을 검증한다.
4. OpenAPI에 노출되는 계약 변경이면 `tests/test_openapi.py`와 문서 예시를 함께 갱신한다.
5. 순수 로직이나 provider adapter는 별도 단위 테스트로 빠르게 검증한다.
