# Python 데코레이터

## 한 줄 정의

데코레이터(decorator)는 함수나 클래스를 받아 부가 기능을 적용하고, 사용할 callable을 반환하는 함수다.

Spring 개발자 관점에서는 다음과 같이 먼저 이해할 수 있다.

> 데코레이터는 원본 코드를 직접 수정하지 않고 함수를 감싸서 기능을 추가하는 문법이다.

다만 모든 데코레이터가 함수를 wrapper로 교체하는 것은 아니다. FastAPI의 `@router.post()`처럼 함수를 프레임워크에 등록한 뒤 원래 함수를 그대로 반환하는 데코레이터도 있다.

## 가장 간단한 예시

```python
def logging(func):
    def wrapper():
        print("시작")
        func()
        print("종료")

    return wrapper


@logging
def hello():
    print("Hello")


hello()
```

실행 결과는 다음과 같다.

```text
시작
Hello
종료
```

`@logging`을 사용한 코드는 실제로 다음 코드와 같은 의미다.

```python
def hello():
    print("Hello")


hello = logging(hello)
```

`logging`은 원래 `hello` 함수를 인자로 받는다. 그리고 원본 함수를 호출하기 전후에 부가 기능을 수행하는 `wrapper`를 반환한다. 마지막으로 `hello`라는 이름이 원본 함수 대신 반환된 `wrapper`를 가리키게 된다.

## 적용 시점과 호출 시점

데코레이터가 적용되는 시점과 장식된 함수가 실행되는 시점은 다르다.

```python
@logging
def hello():
    print("Hello")
```

함수 정의가 완료되면 다음 대입이 실행된다.

```python
hello = logging(hello)
```

모듈 최상위에 함수가 있다면 일반적으로 해당 모듈을 처음 import할 때 적용된다. 이때 `logging(hello)`가 실행되어 `hello`가 `wrapper`로 교체되지만, `wrapper`와 원본 `hello`의 본문은 아직 실행되지 않는다.

```python
hello()
```

이 호출이 발생해야 `wrapper`가 실행되고, 그 안에서 원본 `hello`가 실행된다.

```text
함수 정의
    ↓
logging(원본 hello) 적용
    ↓
hello 이름이 wrapper를 가리킴
    ↓
hello() 호출
    ↓
wrapper 실행
    ↓
원본 hello 실행
```

## Spring AOP와 비슷한 점

Python 데코레이터와 Spring AOP는 모두 원본 비즈니스 코드를 직접 수정하지 않고 부가 관심사를 적용할 수 있다.

```text
부가 기능 실행
    ↓
원본 기능 실행
    ↓
부가 기능 실행
```

대표적인 사용 사례는 다음과 같다.

- 로깅
- 권한 검사
- 실행시간 측정
- 캐싱
- 트랜잭션 처리

따라서 입문 단계에서는 Python 데코레이터를 다음과 같이 생각할 수 있다.

> `@Transactional`과 비슷한 부가 기능을 직접 함수로 구현해 감싸는 느낌

이 비유는 목적을 이해하는 데 유용하지만 실제 동작 구조까지 같다는 뜻은 아니다.

## Spring AOP와 다른 점

### Python 데코레이터

Python 데코레이터는 함수 정의 시점에 대상 함수를 직접 전달받는다.

```python
hello = logging(hello)
```

위 예시에서는 `hello`라는 이름이 데코레이터가 반환한 `wrapper`를 가리키도록 교체된다. 호출자는 별도의 프록시 객체를 통하지 않고 교체된 callable을 직접 호출한다.

### Spring AOP

Spring AOP는 일반적으로 Spring Bean을 프록시 객체로 감싼다. 프록시는 애플리케이션 컨텍스트를 초기화하는 과정에서 생성되고, 부가 기능인 advice는 프록시를 통한 메서드 호출 시 실행된다.

```java
@Transactional
public void save() {
    // 비즈니스 로직
}
```

개념적인 호출 흐름은 다음과 같다.

```text
save() 호출
    ↓
Spring Proxy
    ↓
트랜잭션 시작
    ↓
원본 save() 실행
    ↓
커밋 또는 롤백
```

핵심 차이는 다음과 같다.

| 구분 | Python 데코레이터 | Spring AOP |
|------|-------------------|------------|
| 적용 대상 | 함수 또는 클래스 | 주로 Spring Bean의 메서드 |
| 적용 방식 | 대상 callable을 전달받아 반환값으로 교체하거나 등록 | Bean을 프록시로 감싸 advice 적용 |
| 적용 시점 | 함수·클래스 정의 직후, 일반적으로 모듈 import 시 | 일반적으로 Spring 컨텍스트 초기화 시 프록시 생성 |
| 부가 기능 실행 | 장식된 callable 호출 시 | 프록시를 통한 메서드 호출 시 |
| 프레임워크 필요 여부 | Python 문법만으로 사용 가능 | Spring AOP 인프라 필요 |

Spring AOP는 프록시를 거쳐야 동작하므로 같은 객체 내부에서 자신의 메서드를 직접 호출하는 self-invocation에서는 `@Transactional` 같은 advice가 적용되지 않을 수 있다. 앞의 Python 예시는 함수 이름 자체가 `wrapper`로 교체되므로 동작 방식이 다르다.

AOP는 횡단 관심사를 분리하는 설계 개념이고, 데코레이터는 callable을 변환하거나 등록하는 Python의 구체적인 문법과 실행 구조다. Python 데코레이터 자체가 트랜잭션이나 AOP 프레임워크를 제공하는 것은 아니다.

## 실무적인 데코레이터 작성

실제 함수는 인자를 받거나 값을 반환할 수 있다. 또한 wrapper를 반환하면 원본 함수의 이름과 설명 같은 메타데이터가 사라질 수 있다. 이를 처리하기 위해 `*args`, `**kwargs`와 `functools.wraps`를 사용한다.

```python
from functools import wraps


def logging(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("시작")
        result = func(*args, **kwargs)
        print("종료")
        return result

    return wrapper


@logging
def greet(name: str) -> str:
    return f"안녕하세요, {name}"


print(greet("홍길동"))
```

`functools.wraps`는 원본 함수의 이름, 설명 문자열과 같은 메타데이터를 wrapper에 보존한다. FastAPI처럼 함수의 시그니처와 메타데이터를 검사하는 프레임워크와 함께 사용할 때 특히 중요하다.

## FastAPI의 `@router.post()`

```python
@router.post(
    "/signup/send",
    response_model=ApiResponse[AuthVerificationSendResponse],
)
def signup_send():
    ...
```

이 코드도 데코레이터 문법을 풀어 쓰면 다음과 같다.

```python
def signup_send():
    ...


decorator = router.post(
    "/signup/send",
    response_model=ApiResponse[AuthVerificationSendResponse],
)
signup_send = decorator(signup_send)
```

하지만 앞의 `logging` 예시와 목적이 다르다.

- `logging`은 원본 함수를 호출하는 새로운 `wrapper`를 반환한다.
- `router.post()`는 endpoint 정보를 `APIRouter`에 등록하고 원래 함수를 반환한다.

`router.post(...)`가 만든 데코레이터는 `signup_send` 함수를 전달받아 다음 정보를 router에 등록한다.

- HTTP 메서드 `POST`
- URL 경로 `/signup/send`
- 실제로 호출할 endpoint 함수
- 요청과 응답 모델
- 의존성
- summary와 description 같은 OpenAPI 정보

애플리케이션이 router를 포함하면 FastAPI는 이 등록 정보를 요청 매칭, 의존성 주입, 응답 직렬화와 OpenAPI 생성에 사용한다.

따라서 `@router.post()`는 단순한 메타데이터 표시가 아니다. 함수 정의 시점에 endpoint 등록 동작을 실행하는 등록형 데코레이터다.

## annotation과 decorator 구분

Python과 Java에서 비슷하게 보이는 `@` 문법을 같은 개념으로 보면 안 된다.

- Python decorator: 함수나 클래스를 실제로 전달받아 변환하거나 등록하는 callable
- Python type annotation: `name: str`, `-> int`처럼 타입 또는 메타데이터를 표현하는 문법
- Java annotation: 클래스나 메서드 등에 메타데이터를 부착하고 프레임워크나 컴파일러가 해석하게 하는 기능

한 줄로 정리하면 다음과 같다.

> Python 데코레이터는 함수를 직접 감싸거나 등록하는 실행 가능한 문법이고, Spring AOP는 프록시를 사용해 횡단 관심사를 적용하는 프레임워크 메커니즘이다.
