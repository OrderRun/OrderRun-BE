# Terms Agreement Test Scenarios

기준 테스트 파일: `tests/test_terms_agreement_integration.py`

## 보장 범위

- 약관 동의 생성과 갱신이 같은 사용자 기준으로 동작한다.
- 잘못된 요청은 validation error 계약을 따른다.
- 인증 누락 또는 잘못된 인증은 인증 error 계약을 따른다.
- 약관 동의 모델 필드와 문서 스펙이 일치하는지 확인한다.
