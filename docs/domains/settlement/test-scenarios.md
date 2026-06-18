# Settlement Account Test Scenarios

기준 테스트 파일: `tests/test_settlement_integration.py`

## 보장 범위

- 미등록 계좌 조회는 성공 응답 안에 null 데이터를 반환한다.
- 저장 후 같은 API로 계좌 정보를 수정할 수 있다.
- 인증된 사용자는 정산 계좌 등록에 사용할 은행명 목록을 조회할 수 있다.
- 필수 필드, 형식 validation, 인증 실패를 검증한다.
