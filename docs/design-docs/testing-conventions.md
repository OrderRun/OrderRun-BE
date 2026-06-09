# 테스트 컨벤션

## 목적

이 문서는 OrderRun-BE의 pytest 통합 테스트를 작성할 때 지켜야 할 규칙을 정의한다.

## 규칙

### 1. 테스트 함수명은 행동으로 표현한다

테스트 이름은 **무엇을 검증하는가**를 표현해야 한다. 환경명(`development`, `staging`, `production`), 구현 상세(`test_code`, `bypass`), 내부 메서드명을 그대로 붙이지 않는다.

```python
# bad
def test_login_confirm_accepts_test_code_in_development(): ...
def test_login_confirm_rejects_test_code_in_production(): ...

# good
def test_login_confirm_succeeds_with_verification_bypass_code(): ...
def test_login_confirm_returns_code_mismatch_when_wrong_code_submitted(): ...
```

### 2. 환경명을 테스트 이름에 붙이지 않는다

소스코드는 환경별로 하나다. `monkeypatch`로 `app_env`를 바꿔 테스트하더라도 테스트 이름에 환경명을 포함하지 않는다. 이름에 환경명이 붙으면 "이 환경에서만 동작한다"는 오해를 주고, 환경이 추가될 때 중복 테스트를 양산한다.

### 3. 동일 동작은 한 번만 테스트한다

설정값(`app_env` 등)만 다르고 검증 내용이 동일한 테스트를 분리하지 않는다. 경계 하나당 테스트 하나.

```python
# bad: dev와 staging에서 우회 코드 허용을 따로 테스트
def test_login_confirm_accepts_test_code_in_development(): ...
def test_login_confirm_accepts_test_code_in_staging(): ...

# good: 대표 환경 하나로 행동을 한 번만 검증
def test_login_confirm_succeeds_with_verification_bypass_code(): ...
```

### 4. 시나리오 기반 통합 테스트는 Given-When-Then 구조로 작성한다

테스트 본문을 `# given`, `# when`, `# then` 인라인 코멘트로 구분한다.

```python
def test_login_confirm_succeeds_with_verification_bypass_code(client, sms_sender, monkeypatch):
    # given: 가입된 유저, 비프로덕션 환경
    _signup(client, sms_sender)
    monkeypatch.setattr("app.services.user_auth_service.settings.app_env", "development")
    sent_count = len(sms_sender.sent_messages)

    # when: 우회 인증 코드로 로그인 확인 요청
    response = client.post(
        "/v1/auth/login/confirm",
        json={"phone": "010-1234-5678", "code": "123456"},
    )

    # then: 로그인 성공, SMS 미전송
    assert response.status_code == 200
    assert response.json()["data"]["accessToken"]
    assert len(sms_sender.sent_messages) == sent_count
```
