# Python 모듈 수준 객체

> `app/core/errors.py`를 통해 모듈 수준 변수와 함수, 타입 힌트, 객체 생명 주기를 이해한다.

## 모듈 수준 변수와 함수

클래스나 다른 함수 내부가 아니라 모듈의 최상위에 정의된 이름은 모듈에 속한다.

```python
ERRORS: dict[AppError, ApiErrorSpec] = {
    AppError.USER_NOT_FOUND: ApiErrorSpec(
        404,
        "USER_NOT_FOUND",
        "User not found",
    ),
}


def error_detail(error: AppError, details: str | None = None) -> dict:
    spec = ERRORS[error]
    return {"code": spec.code, "message": spec.message, "details": details}


def api_error(error: AppError, details: str | None = None):
    ...
```

각 이름은 다음과 같이 구분한다.

- `ERRORS`: 모듈 수준 변수 또는 모듈 전역 변수
- `error_detail`, `api_error`: 모듈 수준 함수 또는 모듈 전역 함수

`ERRORS`는 클래스 본문 안에 선언되지 않았으므로 클래스 필드가 아니다. `error_detail`과 `api_error`도 클래스에 속하지 않으므로 메서드가 아니다.

## `ERRORS` 딕셔너리와 타입 힌트

```python
ERRORS: dict[AppError, ApiErrorSpec] = {...}
```

| 부분 | 의미 |
|------|------|
| `ERRORS` | 변수를 가리키는 이름 |
| `:` | 변수 타입 힌트의 시작 |
| `dict[...]` | 키와 값의 대응 관계를 저장하는 딕셔너리 타입 |
| `AppError` | 키 타입 |
| `ApiErrorSpec` | 값 타입 |
| `{...}` | 실제 딕셔너리 객체 |

딕셔너리는 배열이 아니다. Java의 `Map<AppError, ApiErrorSpec>`과 유사하다.

```python
spec = ERRORS[AppError.USER_NOT_FOUND]

spec.http_status  # 404
spec.code         # "USER_NOT_FOUND"
spec.message      # "User not found"
```

`ERRORS`라는 대문자 이름은 실행 중 변경하지 않을 상수처럼 사용한다는 Python 관례다. 그러나 이름을 대문자로 작성했다고 해서 언어 차원에서 변경이 차단되지는 않는다.

## 오류 명세 조회 흐름

`error_detail`과 `api_error`는 같은 `ERRORS` 딕셔너리에서 오류 명세를 조회한다.

```text
AppError.USER_NOT_FOUND
    → ERRORS에서 ApiErrorSpec 조회
    → http_status, code, message 사용
    → HTTPException 생성
```

```python
def error_detail(error: AppError, details: str | None = None) -> dict:
    spec = ERRORS[error]
    return {
        "code": spec.code,
        "message": spec.message,
        "details": details,
    }
```

`ERRORS[error]`에 해당 키가 없다면 일반 딕셔너리 조회와 마찬가지로 `KeyError`가 발생한다. 현재 코드는 모든 `AppError` 사용 값이 `ERRORS`에 등록되어 있다는 전제를 사용한다.

## 생명 주기

`app.core.errors`를 최초로 import하면 Python이 모듈 코드를 실행하면서 `ERRORS` 딕셔너리와 `ApiErrorSpec` 객체들을 생성한다. 모듈은 일반적으로 `sys.modules`에 캐시된다.

```text
sys.modules
    → app.core.errors 모듈
        → ERRORS 딕셔너리
            → ApiErrorSpec 객체들
```

같은 프로세스에서 다른 코드가 `app.core.errors`를 import하면 일반적으로 캐시된 동일한 모듈과 `ERRORS`를 사용한다. 따라서 실행 중 딕셔너리를 변경하면 같은 프로세스의 다른 코드에서도 그 변경을 볼 수 있다.

FastAPI를 여러 worker 프로세스로 실행하면 상황이 다르다. 각 프로세스는 독립된 메모리와 모듈 캐시를 가지므로 worker마다 별도의 `ERRORS`가 생성된다.

## 가비지 컬렉션

Python은 더 이상 참조되지 않는 객체를 정리한다.

- 참조 카운팅: 객체를 가리키는 참조가 0이 되면 정리 대상이 된다.
- 순환 가비지 컬렉터: 객체들이 서로 참조하는 순환 구조를 탐지해 정리한다.

일반적인 서버 실행 중에는 `sys.modules`가 `app.core.errors` 모듈을, 해당 모듈이 `ERRORS`를 계속 참조한다. 따라서 `ERRORS`와 내부 오류 명세는 가비지 컬렉션 대상이 되지 않고 보통 프로세스 종료까지 유지된다.

모듈이 캐시에서 제거되고 외부 참조도 모두 사라진다면 프로세스 종료 전에도 정리 대상이 될 수 있다. 개발 서버 재시작이나 프로세스 종료 시에는 기존 프로세스 메모리 전체가 정리된다.

## 핵심 정리

1. 파일 최상위의 `ERRORS`는 모듈 수준 변수다.
2. 파일 최상위의 `error_detail`, `api_error`는 모듈 수준 함수다.
3. `dict[AppError, ApiErrorSpec]`는 키와 값 타입을 표현한 딕셔너리 타입 힌트다.
4. 모듈이 캐시되는 동안 `ERRORS`도 일반적으로 계속 참조된다.
5. 여러 worker는 하나의 `ERRORS`를 공유하지 않고 프로세스별 객체를 가진다.
