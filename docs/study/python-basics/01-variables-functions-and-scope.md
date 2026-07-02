# Python 변수, 함수와 스코프

> 클래스와 모듈을 배우기 전에 Python의 이름, 함수, 지역·전역 범위를 이해한다.

## 변수는 객체를 가리키는 이름이다

Python에서 변수는 값을 담는 고정된 상자라기보다 객체를 가리키는 이름이다.

```python
name = "OrderRun"
count = 1
```

대입문 왼쪽의 `name`, `count`가 변수 이름이고 오른쪽 표현식의 결과가 연결될 객체다. 같은 이름이 다른 객체를 다시 가리킬 수도 있다.

```python
value = 1
value = "one"
```

Python은 실행 중 타입을 확인하는 동적 타입 언어다. 타입 힌트를 추가하면 코드의 의도를 IDE와 타입 검사기에 전달할 수 있지만, 대입 자체를 런타임에서 강제로 제한하지는 않는다.

```python
count: int = 1
count = "one"  # Python 실행 자체는 허용하지만 타입 검사기는 경고할 수 있다.
```

## 변경 가능한 객체와 변경 불가능한 객체

`int`, `str`, `tuple`은 대표적인 불변 객체이고 `list`, `dict`, `set`은 대표적인 가변 객체다.

```python
items = ["A"]
same_items = items

same_items.append("B")

items  # ["A", "B"]
```

두 이름이 같은 가변 객체를 가리키면 한 이름을 통한 변경이 다른 이름에서도 보인다.

```python
name = "A"
same_name = name

same_name = "B"

name       # "A"
same_name  # "B"
```

문자열 자체를 변경한 것이 아니라 `same_name`이 새 문자열 객체를 가리키도록 다시 대입한 것이다.

## 함수 정의와 호출

함수는 입력을 받아 작업한 뒤 결과를 반환하는 재사용 가능한 코드 단위다.

```python
def add(left: int, right: int) -> int:
    result = left + right
    return result


total = add(1, 2)
```

| 부분 | 의미 |
|------|------|
| `def` | 함수 정의 키워드 |
| `add` | 함수 이름 |
| `left`, `right` | 매개변수 |
| `int` | 매개변수와 반환값의 타입 힌트 |
| `return` | 호출자에게 결과 반환 |
| `add(1, 2)` | 인자를 전달한 함수 호출 |

명시적인 `return`이 없으면 함수는 `None`을 반환한다.

```python
def log_message(message: str) -> None:
    print(message)
```

## 지역 변수

함수 안에서 대입한 이름은 기본적으로 해당 함수의 지역 변수다.

```python
def calculate_total(price: int, quantity: int) -> int:
    subtotal = price * quantity
    return subtotal
```

`price`, `quantity`, `subtotal`은 함수 호출 동안 존재하는 지역 이름이다. 함수 밖에서는 `subtotal`로 접근할 수 없다.

```python
calculate_total(1_000, 2)
subtotal  # NameError
```

## 모듈 전역 변수와 함수

클래스나 함수 내부가 아니라 `.py` 파일 최상위에 정의된 이름은 모듈 수준 이름이다.

```python
# errors.py
DEFAULT_MESSAGE = "Unknown error"


def error_message() -> str:
    return DEFAULT_MESSAGE
```

- `DEFAULT_MESSAGE`: 모듈 수준 변수 또는 모듈 전역 변수
- `error_message`: 모듈 수준 함수 또는 모듈 전역 함수

Python에서 “전역”은 일반적으로 애플리케이션 전체가 공유하는 하나의 공간이 아니라 현재 모듈의 전역 네임스페이스를 뜻한다. 클래스 내부에 정의된 함수만 메서드라고 부르므로 `error_message`는 전역 메서드가 아니다.

## 이름을 찾는 순서: LEGB

Python은 이름을 사용할 때 LEGB 순서로 탐색한다.

1. Local: 현재 함수의 지역 범위
2. Enclosing: 바깥 함수의 범위
3. Global: 현재 모듈의 전역 범위
4. Built-in: `len`, `print` 같은 내장 이름

```python
message = "global"


def outer():
    message = "enclosing"

    def inner():
        message = "local"
        return message

    return inner()
```

`inner()`의 `message`는 가장 가까운 지역 이름인 `"local"`을 가리킨다.

## `global`과 `nonlocal`

함수 안에서 모듈 전역 변수에 새 값을 대입하려면 `global` 선언이 필요하다.

```python
count = 0


def increment() -> None:
    global count
    count += 1
```

중첩 함수에서 바깥 함수의 지역 변수에 대입하려면 `nonlocal`을 사용한다.

```python
def counter():
    count = 0

    def increment() -> int:
        nonlocal count
        count += 1
        return count

    return increment
```

공유 상태를 직접 변경하면 코드 흐름을 추적하기 어려워질 수 있으므로 `global`과 `nonlocal`은 필요한 경우에만 제한적으로 사용한다.

## 상수 이름 관례

Python에는 일반 변수와 별도로 값을 변경하지 못하게 강제하는 `const` 키워드가 없다. 대신 변경하지 않을 모듈 수준 값은 대문자와 밑줄로 작성한다.

```python
DEFAULT_TIMEOUT = 30
MAX_RETRY_COUNT = 3
```

이는 개발자 사이의 관례이며 재대입을 언어 차원에서 막지는 않는다.

## Java와 비교

| 개념 | Java | Python |
|------|------|--------|
| 변수 선언 | `String name = "A";` | `name = "A"` |
| 타입 표시 | 선언에 필수 | 타입 힌트는 선택 사항 |
| 함수 | 클래스의 메서드로 정의 | 모듈 최상위 함수 정의 가능 |
| 지역 변수 | 블록과 메서드 범위 | 함수가 주요 지역 범위 |
| 모듈 전역 변수 | 직접 대응 없음 | 파일 최상위 이름 |
| 상수 관례 | `static final` | 대문자 이름 |

Python의 `if`, `for`, `while` 블록은 별도의 지역 스코프를 만들지 않는다는 점도 Java와 다르다.

```python
if True:
    result = "available"

result  # "available"
```

## 핵심 정리

1. Python 변수는 객체를 가리키는 이름이다.
2. 함수 내부에서 대입한 이름은 기본적으로 지역 변수다.
3. 파일 최상위의 변수와 함수는 모듈 수준 객체다.
4. Python은 이름을 LEGB 순서로 찾는다.
5. `global`과 `nonlocal`은 바깥 범위의 이름에 재대입할 때 사용한다.
