# Python Enum

> Python Enum의 기본 사용법과 문자열 Enum, `app/core/errors.py`의 `AppError`를 이해한다.

## Enum이란?

Enum은 서로 관련된 상수들을 하나의 타입으로 묶는다. Python에서는 표준 라이브러리의 `Enum`을 상속해 정의한다.

```python
from enum import Enum


class Status(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
```

`Status`에는 선언한 멤버만 존재하므로 임의의 문자열을 상태 값처럼 사용하는 것보다 허용 가능한 값의 범위가 명확하다.

```python
status = Status.ACTIVE
```

## 멤버 이름과 값

Enum 멤버는 이름과 값을 각각 가진다.

```python
Status.ACTIVE.name   # "ACTIVE"
Status.ACTIVE.value  # "ACTIVE"
```

대입문의 왼쪽은 멤버 이름이고 오른쪽은 멤버의 실제 값이다.

```python
class Status(Enum):
    ACTIVE = "active"


Status.ACTIVE.name   # "ACTIVE"
Status.ACTIVE.value  # "active"
```

이름과 값은 같을 필요가 없다. 이름은 Python 코드에서 `Status.ACTIVE`로 접근할 때 사용하고, 값은 외부 데이터나 저장 형식과 연결할 때 사용할 수 있다.

## 값으로 Enum 찾기

Enum 클래스를 호출하면 값을 가진 멤버를 찾는다.

```python
Status("active")       # Status.ACTIVE
Status("unknown")      # ValueError
```

이 호출은 새 Enum 멤버를 생성하는 것이 아니다. 이미 선언된 멤버 중 값이 일치하는 대상을 반환한다.

## 일반 Enum과 문자열 비교

일반 Enum 멤버는 문자열 값이 들어 있어도 문자열 객체는 아니다.

```python
from enum import Enum


class Status(Enum):
    ACTIVE = "ACTIVE"


Status.ACTIVE == "ACTIVE"       # False
isinstance(Status.ACTIVE, str)  # False
Status.ACTIVE.value == "ACTIVE" # True
```

문자열 값과 비교하려면 `.value`를 명시적으로 사용한다.

## 문자열 Enum

이 프로젝트의 여러 Enum은 `str`과 `Enum`을 함께 상속한다.

```python
from enum import Enum


class Status(str, Enum):
    ACTIVE = "ACTIVE"
```

클래스 선언의 `(str, Enum)`은 생성자 인자가 아니라 부모 클래스 목록이다. `Status`가 `str`과 `Enum`을 다중 상속한다는 의미다.

```python
Status.ACTIVE == "ACTIVE"       # True
isinstance(Status.ACTIVE, str)  # True
Status.ACTIVE.value             # "ACTIVE"
```

문자열 Enum은 표준 JSON 인코더에서도 문자열 값으로 처리된다.

```python
import json

json.dumps({"status": Status.ACTIVE})
# '{"status": "ACTIVE"}'
```

`print()`나 `str()`의 표현 형식보다 실제 값이 중요할 때는 `.value`를 사용하면 의도가 명확하다.

## `StrEnum`

Python 3.11부터 문자열 Enum 전용인 `StrEnum`을 제공한다. 이 저장소는 Python 3.12 이상을 사용하므로 사용할 수 있다.

```python
from enum import StrEnum


class Status(StrEnum):
    ACTIVE = "ACTIVE"
```

`StrEnum`도 문자열처럼 비교하고 JSON 문자열로 직렬화할 수 있다. 다만 현재 프로젝트 코드가 `class Status(str, Enum)` 패턴을 사용하고 있으므로, 기존 코드를 이해할 때는 두 방식의 목적이 같다는 정도로 구분하면 된다.

## Java Enum과 비교

Java와 Python 모두 문자열 값을 가진 Enum을 만들 수 있지만 상속 구조는 다르다.

```java
public enum PhoneVerificationPurpose {
    SIGNUP("SIGNUP"),
    LOGIN("LOGIN");

    private final String value;

    PhoneVerificationPurpose(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }
}
```

```python
from enum import Enum


class PhoneVerificationPurpose(str, Enum):
    SIGNUP = "SIGNUP"
    LOGIN = "LOGIN"
```

- Java Enum은 암묵적으로 `java.lang.Enum`을 상속하며 `String`을 추가로 상속할 수 없다.
- Java에서는 문자열을 필드에 저장하고 getter로 가져온다.
- Python에서는 `str`과 `Enum`을 실제로 다중 상속한다.

따라서 두 예제는 목적은 비슷하지만 직접 대응하는 상속 문법은 아니다.

## `AppError` 사례

`app/core/errors.py`는 API 오류 종류를 문자열 Enum으로 정의한다.

```python
from enum import Enum


class AppError(str, Enum):
    USER_NOT_FOUND = "USER_NOT_FOUND"
```

```python
AppError.USER_NOT_FOUND.name   # "USER_NOT_FOUND"
AppError.USER_NOT_FOUND.value  # "USER_NOT_FOUND"
```

현재 구현은 코드에서 사용하는 멤버 이름과 오류 식별 문자열을 일관되게 유지하기 위해 같은 값을 사용한다. 반드시 같아야 하는 것은 아니다.

```python
class AppError(str, Enum):
    USER_NOT_FOUND = "user-not-found"


AppError.USER_NOT_FOUND.name   # "USER_NOT_FOUND"
AppError.USER_NOT_FOUND.value  # "user-not-found"
```

`AppError`의 값과 클라이언트에 반환하는 오류 코드는 서로 다른 개념이다. 실제 API 응답의 `code`는 `ERRORS` 딕셔너리에 등록된 `ApiErrorSpec.code`가 결정한다.

```python
ERRORS = {
    AppError.USER_NOT_FOUND: ApiErrorSpec(
        404,
        "USER_NOT_FOUND",
        "User not found",
    ),
}
```

`AppError.USER_NOT_FOUND`는 오류 명세를 조회하는 키이고, `"USER_NOT_FOUND"`는 조회된 명세가 API 응답에 사용하는 코드다.

## 핵심 정리

1. 일반 Enum은 `Enum`을 상속하고 선언된 멤버만 사용한다.
2. `.name`은 멤버 이름이고 `.value`는 멤버가 보유한 값이다.
3. `Status("ACTIVE")`는 값이 일치하는 기존 멤버를 찾는다.
4. 일반 Enum은 문자열과 같지 않지만 `str, Enum` 또는 `StrEnum`은 문자열처럼 동작한다.
5. `AppError`와 `ApiErrorSpec.code`는 역할이 다른 값이다.
