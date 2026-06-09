# 생성 테스트 인벤토리

## 목적

이 문서는 현재 코드베이스에 존재하는 pytest 테스트의 파생 스냅샷이다.
테스트 추가, 삭제, 이동 시 현재 테스트 자산을 빠르게 파악할 수 있도록 파일별 색인으로 관리한다.
도메인별 상세 보장 시나리오는 [`../domains/README.md`](../domains/README.md)를 기준으로 읽는다.

기준 시점은 현재 워킹트리이며, 테스트 수는 `tests/test_*.py` 안의 `test_*` 함수 기준이다.

## 수집 기준

- 테스트 루트: `tests/`
- pytest 설정: `pyproject.toml`의 `[tool.pytest.ini_options]`
- 테스트 파일 패턴: `test_*.py`
- 테스트 함수 패턴: `test_*`
- 현재 테스트 함수 수: 72개
- 현재 테스트 파일 수: 13개
- 지원 파일: `tests/conftest.py`, `tests/factories.py`, `tests/__init__.py`

확인 명령:

```bash
rg -n "^(def test_|async def test_)" tests | wc -l
rg --files tests | sort
```

## 테스트 파일 현황

| 도메인 | 파일 | 테스트 수 | 상세 보장 문서 |
|--------|------|-----------|----------------|
| User/Auth | `tests/test_user_auth_integration.py` | 10 | [`../domains/user-auth/test-scenarios.md`](../domains/user-auth/test-scenarios.md) |
| User/Auth | `tests/test_timestamps.py` | 1 | [`../domains/user-auth/test-scenarios.md`](../domains/user-auth/test-scenarios.md) |
| Terms Agreement | `tests/test_terms_agreement_integration.py` | 4 | [`../domains/terms-agreement/test-scenarios.md`](../domains/terms-agreement/test-scenarios.md) |
| Proposal | `tests/test_proposal_integration.py` | 12 | [`../domains/proposal/test-scenarios.md`](../domains/proposal/test-scenarios.md) |
| Offer/Delivery Flow | `tests/test_offer_integration.py` | 15 | [`../domains/offer/test-scenarios.md`](../domains/offer/test-scenarios.md) |
| Admin/Payment/Settlement Operations | `tests/test_admin_integration.py` | 3 | [`../domains/admin-payment-settlement/test-scenarios.md`](../domains/admin-payment-settlement/test-scenarios.md) |
| Settlement Account | `tests/test_settlement_integration.py` | 3 | [`../domains/settlement/test-scenarios.md`](../domains/settlement/test-scenarios.md) |
| Notification/SMS | `tests/test_notification_integration.py` | 3 | [`../domains/notification/test-scenarios.md`](../domains/notification/test-scenarios.md) |
| Notification/SMS | `tests/test_sms_service.py` | 3 | [`../domains/notification/test-scenarios.md`](../domains/notification/test-scenarios.md) |
| API Contract/OpenAPI | `tests/test_openapi.py` | 11 | [`../domains/api-contract/test-scenarios.md`](../domains/api-contract/test-scenarios.md) |
| API Contract/OpenAPI | `tests/test_errors.py` | 4 | [`../domains/api-contract/test-scenarios.md`](../domains/api-contract/test-scenarios.md) |
| Health/Config | `tests/test_health_integration.py` | 1 | [`../domains/health-config/test-scenarios.md`](../domains/health-config/test-scenarios.md) |
| Health/Config | `tests/test_config.py` | 2 | [`../domains/health-config/test-scenarios.md`](../domains/health-config/test-scenarios.md) |

## 공통 테스트 기반

- `tests/conftest.py`
  - FastAPI `TestClient`를 `OpenApiAssertingClient`로 감싸 성공/실패 응답이 OpenAPI 예시와 호환되는지 요청마다 확인한다.
  - MySQL 테스트 DB에 `Base.metadata.create_all()` / `drop_all()`을 함수 단위로 적용한다.
  - SMS sender와 notification worker를 테스트 대역으로 교체한다.
- `tests/factories.py`
  - 도메인별 통합 테스트에서 사용하는 사용자, proposal, offer, notification 등 테스트 데이터를 생성한다.

## 현재 특이사항

- 프로젝트 가상환경의 `python -m pytest --collect-only -q`는 현재 테스트용 env 또는 `apscheduler` 의존성 누락 시 import 단계에서 실패한다. 실제 pytest 수집과 실행은 테스트용 env와 dev 의존성을 채운 뒤 수행한다.
