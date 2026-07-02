# Python 모듈과 import

> Python에서 모듈이 무엇이며, 다른 모듈의 이름을 현재 파일로 불러오는 방법

## 모듈이란?

Python에서 `.py` 파일 하나는 일반적으로 하나의 모듈(module)이다. 모듈에는 변수, 함수, 클래스처럼 다른 코드에서 재사용할 이름을 정의할 수 있다.

```python
# calculator.py
PI = 3.14


def add(left: int, right: int) -> int:
    return left + right
```

다른 파일에서 `calculator` 모듈을 import하면 그 안에 정의된 이름을 사용할 수 있다.

```python
import calculator

calculator.PI
calculator.add(1, 2)
```

Java의 클래스가 파일 구성의 중심이라면, Python은 파일 자체가 import 가능한 모듈이라는 차이가 있다. 하나의 모듈에 여러 클래스와 함수를 정의할 수 있다.

## 모듈, 패키지, 라이브러리

| 용어 | 의미 | 예시 |
|------|------|------|
| 모듈 | import할 수 있는 Python 코드 단위. 일반적으로 `.py` 파일 하나 | `app/core/errors.py`, `enum` |
| 패키지 | 관련 모듈을 계층적으로 묶은 단위 | `app.core`, `sqlalchemy.orm` |
| 라이브러리 | 특정 기능을 제공하는 코드 모음이라는 일반적인 표현 | Python 표준 라이브러리, SQLAlchemy |

패키지는 여러 모듈을 포함할 수 있다. `app.core.errors`를 예로 들면 `app.core`는 패키지 경로이고 `errors`는 모듈이다.

## import 대상의 종류

Python 코드에서 불러오는 대상은 출처에 따라 구분할 수 있다.

| 종류 | 설명 | 설치 | 예시 |
|------|------|------|------|
| 표준 라이브러리 | Python 설치에 기본 포함 | 불필요 | `enum`, `datetime`, `dataclasses` |
| 외부 패키지 | 프로젝트 의존성으로 별도 설치 | 필요 | `fastapi`, `sqlalchemy` |
| 프로젝트 내부 모듈 | 현재 프로젝트가 정의한 코드 | 불필요 | `app.core.errors` |

```python
from dataclasses import dataclass       # 표준 라이브러리

from fastapi import HTTPException       # 외부 패키지

from app.core.errors import AppError    # 프로젝트 내부 모듈
```

## import 문법

### 모듈 전체 불러오기

```python
import enum


class Status(str, enum.Enum):
    ACTIVE = "ACTIVE"
```

현재 파일에는 `enum`이라는 모듈 이름이 추가된다. 모듈에 속한 이름은 `enum.Enum`처럼 접근한다. 어느 모듈에서 온 이름인지 명확하다는 장점이 있다.

### 모듈에서 특정 이름 불러오기

```python
from enum import Enum


class Status(str, Enum):
    ACTIVE = "ACTIVE"
```

현재 파일에 `Enum`을 직접 추가하므로 `enum.Enum` 대신 `Enum`으로 접근한다.

### 여러 이름 불러오기

```python
from fastapi import HTTPException, status
```

하나의 모듈에서 여러 이름을 가져올 수 있다.

### 별칭 사용하기

```python
from sqlalchemy.orm import Session as DBSession

db = DBSession()
```

`as`는 현재 파일에서 사용할 이름을 바꾼다. 이름 충돌을 피하거나 의미를 명확하게 만들 때 사용한다.

## import할 때 모듈에서 일어나는 일

모듈을 최초로 import하면 Python은 해당 모듈의 최상위 코드를 위에서 아래로 실행한다.

```python
# settings.py
print("settings 모듈 실행")
DEFAULT_TIMEOUT = 30
```

같은 프로세스에서 `settings`를 여러 번 import하더라도 일반적으로 출력은 최초 import 때 한 번만 발생한다. Python이 로드한 모듈을 `sys.modules`에 캐시하기 때문이다.

```text
모듈 검색
    → 최초 import이면 모듈 코드 실행
    → 생성된 모듈 객체를 sys.modules에 저장
    → 이후 import에서는 캐시된 모듈 재사용
```

모듈의 이름을 현재 파일로 가져오는 방식과 무관하게 최초 로딩 원리는 같다.

```python
import settings
from settings import DEFAULT_TIMEOUT
```

개발 서버의 자동 재시작처럼 Python 프로세스 자체가 다시 시작되면 모듈도 새로 로드된다. `importlib.reload()`로 명시적으로 다시 실행하는 경우도 예외다.

## `from __future__ import annotations`

```python
from __future__ import annotations
```

`__future__` import는 향후 Python 동작을 현재 모듈에 적용하기 위한 특별한 import 문법이다. 파일 상단에 작성해야 하며 일반 모듈을 불러오는 import와 목적이 다르다.

이 프로젝트에서는 타입 힌트 평가를 지연하기 위해 사용한다.

```python
from __future__ import annotations


class User:
    def get_friend(self) -> User:
        ...
```

클래스 본문을 실행하는 시점에는 `User` 정의가 아직 끝나지 않았다. annotations 기능을 사용하면 타입 힌트를 즉시 평가하지 않아 자기 자신이나 뒤에서 정의할 타입을 표현하기 쉽다.

```text
User 클래스 본문 실행 시작
    → get_friend 메서드 정의
    → 반환 타입 User 발견
    → User 클래스 정의 완료
```

즉, 반환 타입을 작성하는 시점에는 `User`라는 이름이 아직 완성된 클래스 객체를 가리키지 않는다. `from __future__ import annotations`는 `User` 타입 힌트의 평가를 나중으로 미뤄 이 참조를 가능하게 한다. 이처럼 아직 정의가 끝나지 않았거나 뒤에서 정의될 타입을 먼저 가리키는 것을 전방 참조(forward reference)라고 한다.

이 import를 사용하지 않는다면 필요한 타입만 문자열로 작성할 수도 있다.

```python
class User:
    def get_friend(self) -> "User":
        ...
```

- `from __future__ import annotations`: 현재 파일의 타입 힌트 평가를 전체적으로 지연한다.
- `"User"`: 해당 타입 힌트만 문자열 형태의 전방 참조로 작성한다.

## 핵심 정리

1. Python 모듈은 일반적으로 import 가능한 `.py` 파일 하나다.
2. 패키지는 관련 모듈을 계층적으로 묶는다.
3. `import module`은 모듈 이름을, `from module import name`은 특정 이름을 가져온다.
4. `as`로 현재 파일에서 사용할 별칭을 지정할 수 있다.
5. 모듈은 최초 import 때 실행되고 같은 프로세스에서는 일반적으로 캐시된다.
