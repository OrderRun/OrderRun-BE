# 생성 테스트 인벤토리

## 목적

이 문서는 현재 코드베이스에 존재하는 pytest 테스트의 파생 스냅샷이다.
테스트 추가, 삭제, 이동 시 현재 테스트 자산을 빠르게 파악할 수 있도록 도메인별로 묶어 관리한다.

기준 시점은 현재 워킹트리이며, 테스트 수는 `tests/test_*.py` 안의 `test_*` 함수 기준이다.

## 수집 기준

- 테스트 루트: `tests/`
- pytest 설정: `pyproject.toml`의 `[tool.pytest.ini_options]`
- 테스트 파일 패턴: `test_*.py`
- 테스트 함수 패턴: `test_*`
- 현재 테스트 함수 수: 70개
- 현재 테스트 파일 수: 13개
- 지원 파일: `tests/conftest.py`, `tests/factories.py`, `tests/__init__.py`

확인 명령:

```bash
rg -n "^(def test_|async def test_)" tests | wc -l
rg --files tests | sort
```

## 도메인별 테스트 현황

| 도메인 | 파일 | 테스트 수 | 주요 검증 범위 |
|--------|------|-----------|----------------|
| User/Auth | `tests/test_user_auth_integration.py` | 10 | 회원가입, 로그인, 토큰 갱신/로그아웃, 우회 인증 코드 허용/거부, 사용자 상세, 알림 설정, FCM 토큰, 인증 상태 규칙, SMS 실패 시 인증 저장, 문서 모델 정합성 |
| User/Auth | `tests/test_timestamps.py` | 1 | 전화번호 인증 모델의 ORM timestamp 관리 |
| Terms Agreement | `tests/test_terms_agreement_integration.py` | 4 | 약관 동의 생성/수정, validation error, 인증 error, 문서 모델 정합성 |
| Proposal | `tests/test_proposal_integration.py` | 9 | 공개/내 요청 목록, 상태 필터, 상세 조회, matched timestamp, 생성 계약 검증, validation error, 수정/취소 권한과 상태 규칙, 모델 계약 |
| Offer/Delivery Flow | `tests/test_offer_integration.py` | 13 | offer 생성, proposal offered 전이, 목록/상세/내 목록, accept 상태 전이와 timestamp, active offer 중복 방지, cancel 규칙, 배송 완료 전이, validation/domain error |
| Admin/Payment/Settlement Operations | `tests/test_admin_integration.py` | 5 | payment confirm, holding proposal 검증, offer settlement confirm, completed 상태 검증, disputed offer refund |
| Settlement Account | `tests/test_settlement_integration.py` | 3 | 정산 계좌 미등록 조회, 저장/수정, validation과 인증 |
| Notification/SMS | `tests/test_notification_integration.py` | 3 | root 응답 OpenAPI 예시 정합성, 알림 목록/통계/상세/read 처리, 알림 발송과 실패 케이스 |
| Notification/SMS | `tests/test_sms_service.py` | 3 | AWS SNS 전화번호 포맷, SMS attribute 포함 발송, provider error 전파 |
| API Contract/OpenAPI | `tests/test_openapi.py` | 11 | 한국어 API metadata, 응답 예시 shape, 표준 error wrapper, operation별 성공/error 예시, 대표 계약 예시, request/response body 계약, Mission API 제거 문서화, 반복 status query, DTO 상속 금지 |
| API Contract/OpenAPI | `tests/test_errors.py` | 4 | error catalog 필수 필드, 표준 HTTP exception detail, detail/header 보존, validation catalog message |
| Health | `tests/test_health_integration.py` | 1 | health endpoint의 v1 API 응답 래퍼 |
| Config | `tests/test_config.py` | 2 | OAuth/email 미설정 settings 로드, AWS SNS settings 로드 |

## 공통 테스트 기반

- `tests/conftest.py`
  - FastAPI `TestClient`를 `OpenApiAssertingClient`로 감싸 성공/실패 응답이 OpenAPI 예시와 호환되는지 요청마다 확인한다.
  - MySQL 테스트 DB에 `Base.metadata.create_all()` / `drop_all()`을 함수 단위로 적용한다.
  - SMS sender와 notification worker를 테스트 대역으로 교체한다.
- `tests/factories.py`
  - 도메인별 통합 테스트에서 사용하는 사용자, proposal, offer, notification 등 테스트 데이터를 생성한다.

## 현재 특이사항

- `tests/test_mission_integration.py`는 현재 워킹트리에서 삭제된 상태라 인벤토리에서 제외한다.
- Mission API 제거 회귀는 `tests/test_openapi.py`의 `test_mission_collection_get_is_not_documented`에서 확인한다.
- 로컬 시스템 Python에는 현재 pytest가 설치되어 있지 않아 `python3 -m pytest --collect-only -q`는 실행되지 않았다. 실제 pytest 수집과 실행은 프로젝트 가상환경에 dev 의존성을 설치한 뒤 수행한다.

