# Python 클래스와 상속

> Java/Spring 개발자를 위한 Python 클래스 문법 가이드

## 1. 클래스 정의 문법

### 기본 클래스 (Java와 비교)

**Java:**
```java
public class User {
    private String name;

    public User() {
        this.name = "Guest";
    }
}
```

**Python:**
```python
class User:  # ← 괄호 없음 (상속 없을 때)
    def __init__(self):
        self.name = "Guest"
```

**핵심**:
- Java: `class User { }` - 항상 중괄호
- Python: `class User:` - 콜론(:) 사용, 괄호는 상속 시에만

---

## 2. class PhoneVerificationPurpose(str, enum.Enum) 괄호의 의미

### 괄호 = 상속 (Inheritance)

```python
class PhoneVerificationPurpose(str, enum.Enum):
    SIGNUP = "SIGNUP"
    LOGIN = "LOGIN"
```

**해석**: `PhoneVerificationPurpose`는 `str`과 `enum.Enum`을 **다중 상속**합니다.

### Java와 비교

**Java (인터페이스 다중 구현):**
```java
public enum PhoneVerificationPurpose implements Comparable<PhoneVerificationPurpose> {
    SIGNUP("SIGNUP"),
    LOGIN("LOGIN");

    private final String value;

    PhoneVerificationPurpose(String value) {
        this.value = value;
    }
}
```

**Python (다중 상속):**
```python
class PhoneVerificationPurpose(str, enum.Enum):
    # str을 상속 → 문자열처럼 동작
    # enum.Enum을 상속 → 열거형 기능 획득
    SIGNUP = "SIGNUP"
    LOGIN = "LOGIN"
```

### 왜 str을 상속하는가?

**이유**: JSON 직렬화 및 문자열 비교를 쉽게 하기 위해

```python
# str 상속 안 하면
class Status(enum.Enum):
    ACTIVE = "ACTIVE"

status = Status.ACTIVE
print(status)           # Status.ACTIVE (enum 객체)
print(status.value)     # "ACTIVE" (값 추출 필요)

# str 상속하면
class Status(str, enum.Enum):
    ACTIVE = "ACTIVE"

status = Status.ACTIVE
print(status)           # "ACTIVE" (바로 문자열처럼 동작)
json_data = {"status": status}  # JSON 직렬화 자동 처리
```

**실전 효과:**
```python
# API 응답에서 자동으로 문자열 변환
{
    "purpose": "SIGNUP"  # ← str 상속 덕분에 자동 변환
}
```

---

## 3. class User(Base) - 부모 클래스 상속

### Base란 무엇인가?

```python
from app.core.database import Base

class User(Base):  # ← Base를 상속
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)
```

**Java JPA와 비교:**

**Java:**
```java
@Entity  // ← JPA가 이 어노테이션으로 엔티티 인식
public class User {
    @Id
    private String id;
}
```

**Python SQLAlchemy:**
```python
class User(Base):  # ← Base 상속으로 엔티티 인식
    id = Column(String(36), primary_key=True)
```

### Base 클래스의 정체

**위치**: `app/core/database.py`

```python
from sqlalchemy.orm import declarative_base

Base = declarative_base()  # SQLAlchemy가 제공하는 기본 클래스
```

**Base가 제공하는 기능:**
1. **ORM 매핑 기능** 제공
2. **메타데이터** 관리 (테이블 구조 정보)
3. **쿼리 기능** 활성화

**Spring JPA와 비교:**

| Spring JPA | SQLAlchemy |
|------------|------------|
| `@Entity` 어노테이션 | `Base` 클래스 상속 |
| JPA가 자동 인식 | SQLAlchemy가 자동 인식 |
| `EntityManager`로 쿼리 | `Session`으로 쿼리 |

---

## 4. Python의 다중 상속

### Java vs Python 상속 비교

**Java (다중 상속 불가):**
```java
// ❌ Java는 클래스 다중 상속 불가
public class User extends BaseEntity, Auditable {  // 컴파일 에러
}

// ✅ 인터페이스는 다중 구현 가능
public class User extends BaseEntity implements Serializable, Comparable {
}
```

**Python (다중 상속 가능):**
```python
# ✅ Python은 클래스 다중 상속 가능
class User(Base, TimestampMixin, SoftDeleteMixin):
    pass
```

### 실전 예시: Mixin 패턴

```python
# Mixin: 재사용 가능한 기능 조각
class TimestampMixin:
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class SoftDeleteMixin:
    deleted_at = Column(DateTime, nullable=True)

# 다중 상속으로 기능 조합
class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)
    # created_at, updated_at, deleted_at 자동 상속됨
```

**Java Spring에서의 동일한 패턴:**
```java
@Entity
@EntityListeners(AuditingEntityListener.class)
public class User extends BaseTimeEntity implements SoftDeletable {
    // BaseTimeEntity → createdAt, updatedAt
    // SoftDeletable → deletedAt
}
```

---

## 5. 클래스 정의 패턴 정리

### 패턴 1: 상속 없음

```python
class SimpleClass:
    pass
```

### 패턴 2: 단일 상속

```python
class User(Base):  # Base만 상속
    pass
```

### 패턴 3: 다중 상속

```python
class Status(str, enum.Enum):  # str과 enum.Enum 둘 다 상속
    ACTIVE = "ACTIVE"
```

### 패턴 4: Mixin 패턴 (다중 상속 활용)

```python
class User(Base, TimestampMixin, SoftDeleteMixin):
    pass
```

---

## 6. 상속 순서의 중요성 (MRO - Method Resolution Order)

```python
class A:
    def greet(self):
        print("A")

class B:
    def greet(self):
        print("B")

class C(A, B):  # ← 상속 순서: A가 먼저
    pass

c = C()
c.greet()  # "A" 출력 (A가 B보다 우선)
```

**SQLAlchemy에서의 순서:**
```python
class User(Base, TimestampMixin):  # ← Base가 최우선
    pass

# Base가 먼저 와야 SQLAlchemy가 정상 동작
```

---

## 핵심 정리

| 항목 | Java | Python |
|------|------|--------|
| **클래스 정의** | `class User { }` | `class User:` |
| **단일 상속** | `extends BaseEntity` | `class User(Base):` |
| **다중 상속** | ❌ 불가 (인터페이스만 가능) | ✅ 가능 |
| **괄호 의미** | - | 상속할 부모 클래스 지정 |
| **Enum** | `enum` 키워드 | `enum.Enum` 상속 |
| **ORM 엔티티** | `@Entity` 어노테이션 | `Base` 클래스 상속 |

**핵심 원칙:**
1. 괄호 안 = 상속할 부모 클래스
2. 다중 상속 가능 (순서 중요)
3. `Base` 상속 = SQLAlchemy 엔티티
4. `str, enum.Enum` = 문자열 Enum
