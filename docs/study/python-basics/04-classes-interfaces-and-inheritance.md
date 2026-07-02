# Python 클래스, 인터페이스와 상속

> 클래스와 인스턴스부터 Python의 인터페이스 표현 방법, 상속과 MRO까지 설명한다.

## 클래스와 인스턴스

클래스는 객체가 가질 데이터와 동작을 정의한다. 클래스를 호출하면 해당 클래스의 인스턴스가 만들어진다.

```python
class User:
    pass


user = User()
```

- `User`: 클래스
- `user`: `User` 클래스의 인스턴스를 가리키는 변수
- `User()`: 인스턴스 생성

Java와 달리 상속하지 않는 Python 클래스는 이름 뒤에 괄호를 생략할 수 있다.

```java
public class User {
}
```

```python
class User:
    pass
```

## `__init__`과 `self`

`__init__`은 생성된 인스턴스의 초기 상태를 설정하는 특수 메서드다.

```python
class User:
    def __init__(self, name: str):
        self.name = name


user = User("Alice")
user.name  # "Alice"
```

`self`는 메서드가 동작할 현재 인스턴스를 가리킨다. 호출할 때는 Python이 인스턴스를 첫 번째 인자로 전달하므로 `user.get_name()`처럼 사용한다.

```python
class User:
    def __init__(self, name: str):
        self.name = name

    def get_name(self) -> str:
        return self.name
```

`self`는 예약어는 아니지만 다른 이름으로 바꾸지 않는 것이 Python의 표준 관례다.

## 인스턴스 속성과 클래스 속성

`self.name`처럼 인스턴스에 대입한 값은 인스턴스 속성이다. 클래스 본문에 직접 정의한 값은 클래스 속성이다.

```python
class User:
    category = "member"

    def __init__(self, name: str):
        self.name = name
```

```python
User.category  # "member"

alice = User("Alice")
bob = User("Bob")

alice.name  # "Alice"
bob.name    # "Bob"
```

가변 객체를 클래스 속성으로 두면 모든 인스턴스가 같은 객체를 공유할 수 있으므로 주의해야 한다.

## 메서드의 종류

```python
class User:
    category = "member"

    def instance_method(self) -> str:
        return self.category

    @classmethod
    def class_method(cls) -> str:
        return cls.category

    @staticmethod
    def normalize_name(name: str) -> str:
        return name.strip()
```

| 종류 | 첫 번째 인자 | 주 용도 |
|------|--------------|---------|
| 인스턴스 메서드 | `self` | 인스턴스 상태 사용 |
| 클래스 메서드 | `cls` | 클래스 상태 사용, 대체 생성자 |
| 정적 메서드 | 자동 전달 없음 | 클래스와 관련된 독립 로직 |

파일 최상위의 함수는 이 세 메서드와 달리 특정 클래스에 속하지 않는 모듈 수준 함수다.

## Python에 Java `interface`가 있는가?

Python에는 Java의 `interface` 키워드와 완전히 같은 문법이 없다. 필요한 계약의 성격에 따라 duck typing, `Protocol`, `ABC`를 선택한다.

세 개념을 모두 상속 방법으로 보면 안 된다.

- Duck typing: 객체를 사용하는 Python의 동작 방식
- `Protocol`: 객체의 구조를 표현하는 정적 타입 계약
- `ABC`: 명시적 상속 관계와 런타임 제약을 제공하는 추상 기반 클래스

## Duck typing

Duck typing은 객체의 선언된 타입이나 상속 관계보다 필요한 동작을 실제로 제공하는지를 기준으로 사용하는 방식이다.

```python
class ConsoleSender:
    def send(self, message: str) -> None:
        print(message)


class RecordingSender:
    def __init__(self):
        self.messages: list[str] = []

    def send(self, message: str) -> None:
        self.messages.append(message)


def notify(sender, message: str) -> None:
    sender.send(message)
```

`ConsoleSender`와 `RecordingSender`는 공통 부모를 상속하지 않았다. 그러나 둘 다 `send()`를 제공하므로 `notify()`에서 사용할 수 있다.

```python
notify(ConsoleSender(), "Hello")

recording_sender = RecordingSender()
notify(recording_sender, "Hello")
```

필요한 동작이 없으면 실제 호출 시점에 오류가 발생한다.

```python
class InvalidSender:
    pass


notify(InvalidSender(), "Hello")
# AttributeError: 'InvalidSender' object has no attribute 'send'
```

### EAFP

Duck typing은 Python의 EAFP(Easier to Ask Forgiveness than Permission) 방식과 함께 사용되는 경우가 많다. 호출 전에 모든 조건을 검사하기보다 일단 올바른 인터페이스를 제공한다고 보고 사용한 뒤, 필요한 위치에서 예외를 처리한다.

```python
try:
    sender.send("Hello")
except AttributeError:
    ...
```

다음처럼 `hasattr()`만 확인하는 방식은 `send`가 실제로 호출 가능한지, 올바른 인자를 받는지까지 보장하지 않는다.

```python
if hasattr(sender, "send"):
    sender.send("Hello")
```

모든 `AttributeError`를 잡는 것도 위험하다. `send()` 내부에서 발생한 별개의 `AttributeError`까지 잘못 처리할 수 있기 때문이다. 예외를 잡아 복구할 명확한 이유가 없다면 호출자가 오류를 확인하도록 두는 편이 낫다.

### 언제 사용하는가?

- 작은 내부 함수에서 필요한 동작이 명확할 때
- 테스트 대역을 간단하게 만들어 교체할 때
- 정적 타입 계약보다 유연성이 중요한 코드

이 저장소의 테스트에 있는 `RecordingSmsSender`, `FailingSmsSender`도 별도의 기반 클래스를 상속하지 않고 필요한 `send()` 메서드만 제공한다. 런타임 관점에서는 duck typing으로 동작한다.

## `Protocol`

`Protocol`은 객체가 제공해야 할 속성과 메서드를 타입 힌트로 표현한다. 구현 클래스가 Protocol을 직접 상속하지 않아도 구조가 일치하면 계약을 만족한다. 이를 구조적 서브타이핑(structural subtyping)이라고 한다.

이 저장소의 `SmsSender`가 실제 사례다.

```python
from typing import Protocol


class SmsSender(Protocol):
    def send(self, phone: str, message: str) -> None:
        """Send an SMS message."""
```

실제 AWS 구현체는 `SmsSender`를 상속하지 않는다.

```python
class AwsSnsSmsSender:
    def send(self, phone: str, message: str) -> None:
        ...


def send_verification(sender: SmsSender) -> None:
    sender.send("01012345678", "인증번호: 123456")
```

정적 타입 검사기는 `AwsSnsSmsSender`에 호환되는 `send()`가 있으므로 `SmsSender` 계약을 만족한다고 판단할 수 있다. 테스트 구현도 같은 방식으로 교체할 수 있다.

```python
class RecordingSmsSender:
    def __init__(self):
        self.sent_messages: list[dict] = []

    def send(self, phone: str, message: str) -> None:
        self.sent_messages.append(
            {"phone": phone, "message": message},
        )
```

### Protocol이 검사되는 시점

`Protocol`은 기본적으로 정적 타입 검사기와 IDE를 위한 계약이다. Python 런타임은 일반 Protocol 타입 힌트만으로 잘못된 구현의 인스턴스 생성을 차단하지 않는다.

```python
class InvalidSender:
    pass


sender: SmsSender = InvalidSender()
# Python 실행 자체는 이 대입을 허용한다.
# 정적 타입 검사기는 send()가 없다는 오류를 보고할 수 있다.
```

런타임에서 `isinstance()` 확인이 꼭 필요하다면 `@runtime_checkable`을 추가할 수 있다.

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class SmsSender(Protocol):
    def send(self, phone: str, message: str) -> None:
        ...


isinstance(RecordingSmsSender(), SmsSender)  # True
```

이 런타임 검사는 필요한 속성의 존재 여부를 중심으로 확인한다. 매개변수 타입과 반환 타입 등 전체 시그니처가 정확히 호환되는지까지 검증하지 않으므로 정적 타입 검사를 대체하지 않는다.

### 언제 사용하는가?

- 외부 API, 메시지 발송기, 저장소처럼 구현체를 교체해야 할 때
- 구현 클래스에 특정 기반 클래스 상속을 강제하고 싶지 않을 때
- 운영 구현과 테스트 대역에 같은 정적 타입 계약을 적용할 때
- 공통 구현이나 공통 인스턴스 상태를 물려줄 필요가 없을 때

FastAPI 서비스에서 의존성의 최소 계약을 표현할 때는 일반적으로 `Protocol`이 실용적이다.

## `ABC`와 `abstractmethod`

`ABC`는 Abstract Base Class의 약자다. 하위 클래스가 구현해야 할 메서드를 명시하고, 구현하지 않은 클래스의 인스턴스 생성을 런타임에서 막는다. 구현체는 ABC를 직접 상속해야 하므로 명목적 서브타이핑(nominal subtyping)에 해당한다.

```python
from abc import ABC, abstractmethod


class MessageSender(ABC):
    @abstractmethod
    def send(self, message: str) -> None:
        ...
```

추상 메서드를 구현한 하위 클래스는 인스턴스를 만들 수 있다.

```python
class ConsoleSender(MessageSender):
    def send(self, message: str) -> None:
        print(message)


ConsoleSender()  # 생성 가능
```

구현하지 않은 하위 클래스는 클래스 정의 자체는 가능하지만 인스턴스를 만드는 시점에 `TypeError`가 발생한다.

```python
class InvalidSender(MessageSender):
    pass


InvalidSender()
# TypeError: Can't instantiate abstract class InvalidSender ...
```

### 추상 property

메서드뿐 아니라 property 구현도 요구할 수 있다.

```python
class MessageSender(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    def send(self, message: str) -> None:
        ...
```

### 공통 구현 제공

ABC는 계약뿐 아니라 하위 클래스가 함께 사용할 상태와 concrete method를 제공할 수 있다.

```python
class MessageSender(ABC):
    def __init__(self, sender_name: str):
        self.sender_name = sender_name

    def send_with_prefix(self, message: str) -> None:
        self.send(f"[{self.sender_name}] {message}")

    @abstractmethod
    def send(self, message: str) -> None:
        ...
```

이 점에서 `ABC`는 순수한 Java interface보다는 공통 구현을 가진 Java 추상 클래스에 더 가깝다.

### 언제 사용하는가?

- 모든 구현체가 공통 상태나 구현을 상속받아야 할 때
- 구현체가 같은 클래스 계층에 속한다는 사실이 중요할 때
- 필수 구현이 빠진 클래스의 인스턴스 생성을 런타임에서 차단할 때
- 템플릿 메서드 같은 상속 기반 확장 구조가 필요할 때

공통 구현이 필요하지 않고 타입 계약만 필요하다면 `ABC`보다 `Protocol`의 결합도가 낮다.

## 세 방식 비교

| 기준 | Duck typing | `Protocol` | `ABC` |
|------|-------------|------------|-------|
| 명시적 상속 필요 | 없음 | 없음 | 필요 |
| 정적 타입 계약 | 없음 | 제공 | 제공 가능 |
| 런타임 구현 강제 | 호출 시 실패 | 기본적으로 없음 | 인스턴스 생성 시 검사 |
| 공통 구현·상태 제공 | 없음 | 주 목적이 아님 | 적합 |
| 구현체 결합도 | 가장 낮음 | 낮음 | 높음 |
| 테스트 대역 작성 | 매우 쉬움 | 쉬움 | ABC 상속과 구현 필요 |

선택 순서는 다음과 같이 정리할 수 있다.

1. 단순히 필요한 동작을 호출하면 충분하다면 duck typing을 사용한다.
2. 타입 검사 가능한 명시적 계약이 필요하지만 상속을 강제하고 싶지 않다면 `Protocol`을 사용한다.
3. 공통 구현을 상속하거나 미구현 인스턴스 생성을 런타임에 막아야 한다면 `ABC`를 사용한다.

Duck typing과 `Protocol`은 명시적인 클래스 상속 없이도 사용할 수 있다. 세 방식 중 `ABC`만 구현체의 상속 구조에 직접 참여한다.

| Java | Python |
|------|--------|
| `interface` 명시적 구현 | `Protocol` 구조적 계약 또는 `ABC` 명시적 상속 |
| `implements` | 별도 키워드 없음 |
| 추상 클래스 | 공통 구현을 가진 `ABC` |
| 컴파일러 계약 검사 | 정적 타입 검사기 또는 ABC 인스턴스화 시 검사 |

## 단일 상속

부모 클래스를 클래스 이름 뒤 괄호 안에 작성한다.

```python
class Animal:
    def speak(self) -> str:
        return "sound"


class Dog(Animal):
    pass


Dog().speak()  # "sound"
```

Python의 `class Dog(Animal)`은 Java의 `class Dog extends Animal`에 해당한다.

## 메서드 재정의와 `super()`

하위 클래스는 부모 메서드를 같은 이름으로 다시 정의할 수 있다.

```python
class Animal:
    def __init__(self, name: str):
        self.name = name

    def speak(self) -> str:
        return "sound"


class Dog(Animal):
    def __init__(self, name: str):
        super().__init__(name)

    def speak(self) -> str:
        return "bark"
```

`super()`는 단순히 “직접 부모”를 고정해서 부르는 표현이 아니라 MRO상 다음 클래스에 메서드 호출을 위임한다. 다중 상속에서 각 클래스가 협력하려면 `super()`를 일관되게 사용하는 것이 중요하다.

## SQLAlchemy `Base` 상속

이 프로젝트의 모델은 SQLAlchemy가 제공하는 기반 클래스를 상속한다.

```python
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
```

`Base`를 상속하면 SQLAlchemy가 클래스를 ORM 모델로 등록하고 테이블 메타데이터를 수집한다. Java의 `@Entity`와 목적은 유사하지만 Python에서는 기반 클래스 상속을 사용하는 구조다.

## 다중 상속

Python 클래스는 여러 부모 클래스를 상속할 수 있다.

```python
class TimestampMixin:
    created_at = None
    updated_at = None


class SoftDeleteMixin:
    deleted_at = None


class User(Base, TimestampMixin, SoftDeleteMixin):
    pass
```

Java는 여러 클래스를 동시에 상속할 수 없고 여러 인터페이스만 구현할 수 있다. Python은 클래스 다중 상속이 가능하며, 작은 재사용 기능을 제공하는 Mixin 패턴에 자주 사용한다.

## MRO

MRO(Method Resolution Order)는 다중 상속에서 속성과 메서드를 찾는 순서다.

```python
class A:
    def greet(self) -> str:
        return "A"


class B:
    def greet(self) -> str:
        return "B"


class C(A, B):
    pass


C().greet()  # "A"
C.mro()      # [C, A, B, object]
```

Python은 단순히 왼쪽 부모만 반복해서 탐색하지 않고 C3 linearization 규칙으로 일관된 MRO를 계산한다. 실제 탐색 순서는 `ClassName.mro()`로 확인할 수 있다.

## 핵심 정리

1. 클래스는 데이터와 동작을 정의하고, 클래스를 호출하면 인스턴스가 생성된다.
2. `self`는 현재 인스턴스, `cls`는 현재 클래스를 가리킨다.
3. Python에는 Java의 `interface` 키워드가 없으며 duck typing, `ABC`, `Protocol`을 사용한다.
4. 괄호 안에는 상속할 부모 클래스를 작성한다.
5. Python은 클래스 다중 상속을 지원하고 MRO에 따라 메서드를 찾는다.
