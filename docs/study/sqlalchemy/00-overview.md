# SQLAlchemy 개요

> Java/Spring 개발자를 위한 SQLAlchemy ORM 입문

## SQLAlchemy란?

SQLAlchemy는 Python에서 관계형 데이터베이스를 다루는 라이브러리다. 이 프로젝트에서는 ORM(Object-Relational Mapping)을 사용해 데이터베이스 테이블과 Python 클래스를 연결한다.

Java/Spring 환경의 JPA와 Hibernate가 담당하는 역할과 유사하다.

| Java/Spring | Python |
|-------------|--------|
| JPA 인터페이스와 매핑 annotation | SQLAlchemy ORM API |
| Hibernate 구현체 | SQLAlchemy ORM과 SQL 표현 계층 |
| `EntityManager` | `Session` |
| JPQL 또는 Criteria API | SQLAlchemy의 `select()`와 표현식 |

두 기술의 API와 내부 동작이 동일한 것은 아니다. 이 비교는 담당하는 역할을 이해하기 위한 것이다.

## 주요 역할

SQLAlchemy ORM은 다음 작업을 담당한다.

1. 데이터베이스 테이블과 Python 클래스 매핑
2. 컬럼 타입과 제약조건 선언
3. 엔티티 사이의 관계 표현
4. Python 표현식으로 쿼리 작성
5. 세션을 통한 영속성 및 트랜잭션 관리

## 모델과 컬럼 매핑

```python
from sqlalchemy import Column, String


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
```

`User` 클래스는 `users` 테이블에 대응하고, `Column()`은 각 Python 속성을 데이터베이스 컬럼에 연결한다. 저장소 일부 모델은 SQLAlchemy 2.x의 `Mapped`와 `mapped_column()` 표기법도 사용하지만 역할은 같다.

컬럼 타입, 기본 키, NULL 허용 여부, 고유 제약조건 등의 자세한 내용은 [`01-column-class.md`](./01-column-class.md)를 참고한다.

## 관계 매핑

```python
from sqlalchemy.orm import relationship


class User(Base):
    device_tokens = relationship(
        "DeviceToken",
        back_populates="user",
    )
```

`relationship()`은 모델 사이의 객체 관계를 표현한다. 외래 키 컬럼 자체와는 역할이 다르며, 양방향 연결, 로딩 전략, cascade 등을 설정할 수 있다.

관계 유형과 파라미터의 자세한 내용은 [`02-relationship.md`](./02-relationship.md)를 참고한다.

## 쿼리와 세션

```python
from sqlalchemy import select
from sqlalchemy.orm import Session


def find_user(db: Session, user_id: str) -> User | None:
    statement = select(User).where(User.id == user_id)
    return db.scalar(statement)
```

`Session`은 쿼리 실행과 ORM 객체의 상태를 관리한다. 데이터 변경 작업에서는 `commit()`과 `rollback()`을 통해 트랜잭션 경계를 관리한다.

```python
try:
    db.add(user)
    db.commit()
except Exception:
    db.rollback()
    raise
```

## import와의 관계

SQLAlchemy는 외부 패키지이므로 프로젝트 의존성으로 설치되어 있어야 한다. 설치 후 필요한 이름을 모듈에서 import한다.

```python
from sqlalchemy import select
from sqlalchemy.orm import Session, relationship
```

`from sqlalchemy import ...`은 Python import 문법이고, 불러온 `select`, `Session`, `relationship`의 기능은 SQLAlchemy가 제공한다. import 문법과 라이브러리 자체의 역할을 구분해야 한다.

## 핵심 정리

1. SQLAlchemy는 Python에서 관계형 데이터베이스를 다루는 라이브러리다.
2. ORM을 사용하면 테이블을 Python 클래스로 매핑할 수 있다.
3. 컬럼, 관계, 쿼리, 세션과 트랜잭션 관리 기능을 제공한다.
4. Java의 JPA/Hibernate와 역할은 유사하지만 API와 동작이 동일하지는 않다.
