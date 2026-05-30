# Python Import와 모듈 시스템

> Java/Spring 개발자를 위한 Python 가이드

## 1. import enum - Python 표준 라이브러리

### Java와 비교

**Java의 Enum:**
```java
public enum PhoneVerificationPurpose {
    SIGNUP,
    LOGIN
}
```

**Python의 Enum (표준 라이브러리):**
```python
import enum  # Python 내장 라이브러리 (별도 설치 불필요)

class PhoneVerificationPurpose(str, enum.Enum):
    SIGNUP = "SIGNUP"
    LOGIN = "LOGIN"
```

### enum은 라이브러리인가?

**답: 네, Python 표준 라이브러리입니다.**

- **위치**: Python 설치 시 기본 포함 (`import enum`만으로 사용 가능)
- **용도**: Java의 Enum과 동일하게 상수 그룹 정의
- **설치 불필요**: `pip install` 없이 바로 사용 가능

### Python 라이브러리 종류

| 종류 | 설명 | 설치 방법 | 예시 |
|------|------|-----------|------|
| **표준 라이브러리** | Python 기본 포함 | 설치 불필요 | `enum`, `datetime`, `hashlib` |
| **외부 라이브러리** | 별도 설치 필요 | `pip install` | `fastapi`, `sqlalchemy` |
| **프로젝트 내부** | 내가 만든 모듈 | 없음 | `app.models.user` |

### 예시: user.py의 import 구분

```python
# 1. Python 표준 라이브러리 (설치 불필요)
from __future__ import annotations  # Python 기능 활성화
import enum                          # 열거형
import uuid                          # UUID 생성
from datetime import datetime        # 날짜/시간

# 2. 외부 라이브러리 (pip install 필요)
from sqlalchemy import Column        # ORM - pip install sqlalchemy
from sqlalchemy.orm import relationship

# 3. 프로젝트 내부 모듈
from app.core.database import Base  # 내가 만든 Base 클래스
```

---

## 2. from sqlalchemy는 무엇인가?

### Java/Spring과 비교

**Spring JPA (Java):**
```java
import javax.persistence.*;  // JPA 어노테이션

@Entity
@Table(name = "users")
public class User {
    @Id
    @Column(name = "id")
    private String id;
}
```

**SQLAlchemy (Python):**
```python
from sqlalchemy import Column, String  # ORM 도구
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)
```

### SQLAlchemy란?

| 항목 | 설명 |
|------|------|
| **정의** | Python용 ORM (Object-Relational Mapping) 라이브러리 |
| **Spring 비교** | Java의 Hibernate/JPA와 동일한 역할 |
| **설치** | `pip install sqlalchemy` |
| **버전** | 이 프로젝트는 SQLAlchemy 2.x 사용 |

### SQLAlchemy 주요 기능

```python
# 1. Column 정의 (JPA @Column과 동일)
from sqlalchemy import Column, String, Integer, Boolean, DateTime

id = Column(String(36), primary_key=True)        # @Id
name = Column(String(100), nullable=False)       # @Column(nullable=false)
phone = Column(String(20), unique=True)          # @Column(unique=true)

# 2. 관계 매핑 (JPA @OneToMany, @ManyToOne과 동일)
from sqlalchemy.orm import relationship

device_tokens = relationship("DeviceToken", back_populates="user")
# JPA의 @OneToMany(mappedBy = "user")와 동일

# 3. 쿼리 실행 (EntityManager와 동일)
from sqlalchemy.orm import Session

db = Session()  # EntityManager와 유사
user = db.query(User).filter(User.phone == "010-1234-5678").first()
# JPQL: SELECT u FROM User u WHERE u.phone = :phone
```

### 용도 요약

**SQLAlchemy는 다음 작업을 수행합니다:**
1. **DB 테이블 ↔ Python 클래스** 매핑 (ORM)
2. **SQL 쿼리를 Python 코드로** 작성 가능
3. **트랜잭션 관리** (`db.commit()`, `db.rollback()`)
4. **관계 매핑** (1:N, N:1, N:M)

---

## 3. import 문법 정리

### 3-1. import vs from...import

```python
# 방법 1: 모듈 전체 가져오기
import enum
value = enum.Enum  # 모듈명.클래스명

# 방법 2: 특정 클래스만 가져오기
from enum import Enum
value = Enum  # 바로 사용 가능

# 방법 3: 여러 개 가져오기
from sqlalchemy import Column, String, Integer

# 방법 4: 별칭 사용
from sqlalchemy.orm import Session as DBSession
db = DBSession()  # Session 대신 DBSession으로 사용
```

### 3-2. __future__ import는 뭐지?

```python
from __future__ import annotations
```

**용도**: Python의 미래 기능을 현재 버전에서 미리 활성화

**예시: Type Annotation 순환 참조 해결**
```python
# __future__ import 없으면 에러 발생
class User:
    def get_friend(self) -> User:  # ❌ User가 아직 정의 안 됨
        pass

# __future__ import 있으면 정상 동작
from __future__ import annotations

class User:
    def get_friend(self) -> User:  # ✅ 문자열로 처리되어 OK
        pass
```

---

## 4. Java vs Python 라이브러리 비교

| Java (Spring) | Python (FastAPI) | 역할 |
|---------------|------------------|------|
| `javax.persistence.*` | `sqlalchemy` | ORM (DB 매핑) |
| `org.springframework.web.bind.annotation.*` | `fastapi` | REST API |
| `java.util.UUID` | `uuid` | UUID 생성 |
| `java.time.LocalDateTime` | `datetime` | 날짜/시간 |
| `javax.validation.*` | `pydantic` | 데이터 검증 |
| `org.springframework.beans.factory.annotation.*` | `fastapi.Depends` | 의존성 주입 |

---

## 핵심 정리

1. **enum**: Python 표준 라이브러리, 설치 불필요
2. **sqlalchemy**: 외부 ORM 라이브러리, JPA/Hibernate와 동일한 역할
3. **import**: Java의 `import`와 동일, 모듈 가져오기
4. **from...import**: 특정 클래스/함수만 선택적으로 가져오기
