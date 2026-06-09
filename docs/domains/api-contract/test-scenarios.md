# API Contract/OpenAPI Test Scenarios

기준 테스트 파일: `tests/test_openapi.py`, `tests/test_errors.py`

## 보장 범위

- OpenAPI metadata와 대표 성공/실패 예시 shape가 한국어 API 문서 기준과 일치한다.
- validation error와 표준 HTTP exception detail이 error wrapper 계약을 따른다.
- operation별 성공 예시와 표준 error 예시가 존재한다.
- 인증, 관리자 결제 확인, Offer 수락 등 대표 request/response 계약을 검증한다.
- Mission collection API가 문서화되지 않음을 확인한다.
- 반복 `status` query parameter가 array query로 노출된다.
- API schema가 다른 API DTO를 상속하지 않는 규칙을 확인한다.
- error catalog 필수 필드, details/header 보존, validation catalog message를 검증한다.
