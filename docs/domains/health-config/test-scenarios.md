# Health/Config Test Scenarios

기준 테스트 파일: `tests/test_health_integration.py`, `tests/test_config.py`

## 보장 범위

- health endpoint가 v1 `ApiResponse` 구조를 반환한다.
- OAuth/email 값 없이도 settings 객체를 구성할 수 있다.
- AWS SNS region, access key, secret key, sender id, SMS type 설정이 로드된다.
