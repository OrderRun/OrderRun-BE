# SQLAlchemy Column 클래스 완벽 가이드

> Java JPA @Column 어노테이션과 비교하여 설명

## Column 클래스 개요

SQLAlchemy의 `Column`은 데이터베이스 테이블의 컬럼을 정의하는 클래스입니다.
**Java JPA의 `@Column` 어노테이션과 동일한 역할**을 합니다.

---

## 1. 기본 사용법

### Java JPA와 비교

**Java JPA:**
```java
@Entity
public class User {
    @Id
    @Column(name = "id", length = 36, nullable = false)
    private String id;

    @Column(name = "name", length = 100, nullable = false)
    private String name;

    @Column(name = "phone", length = 20, unique = true)
    private String phone;
}
```

**SQLAlchemy:**
```python
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, nullable=False)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True)
```

---

## 2. Column 생성자 파라미터 (주요 파라미터만)

### 2-1. name (컬럼 이름)

**Java:**
```java
@Column(name = "user_name")
private String userName;
```

**Python:**
```python
user_name = Column("user_name", String(100))  # 위치 인자
# 또는
user_name = Column(String(100), name="user_name")  # 키워드 인자
```

**기본 동작**: name을 생략하면 **Python 변수명**이 컬럼명이 됩니다.
```python
phone = Column(String(20))  # ← 컬럼명은 "phone"
```

**대소문자 처리**:
- 소문자만: 따옴표 없이 처리 (case-insensitive)
- 대문자 포함: 따옴표로 감싸서 처리 (case-sensitive)

---

### 2-2. type_ (컬럼 타입)

**Java:**
```java
@Column(columnDefinition = "VARCHAR(100)")
private String name;

@Column(columnDefinition = "INT")
private Integer age;
```

**Python:**
```python
name = Column(String(100))  # VARCHAR(100)
age = Column(Integer)       # INT
created_at = Column(DateTime(timezone=True))  # TIMESTAMP WITH TIMEZONE
```

**주요 타입:**

| Java | SQLAlchemy | SQL |
|------|------------|-----|
| `String` | `String(length)` | VARCHAR |
| `Integer` | `Integer` | INT |
| `Long` | `BigInteger` | BIGINT |
| `Boolean` | `Boolean` | BOOLEAN/TINYINT |
| `LocalDateTime` | `DateTime` | DATETIME/TIMESTAMP |
| `BigDecimal` | `Numeric(precision, scale)` | DECIMAL |
| `byte[]` | `LargeBinary` | BLOB |

---

### 2-3. primary_key (기본 키)

**Java:**
```java
@Id
@GeneratedValue(strategy = GenerationType.IDENTITY)
private Long id;
```

**Python:**
```python
id = Column(BigInteger, primary_key=True, autoincrement=True)
```

**복합 키 (Composite Key):**
```python
class UserRole(Base):
    user_id = Column(String(36), primary_key=True)
    role_id = Column(String(36), primary_key=True)
```

---

### 2-4. nullable (NULL 허용 여부)

**Java:**
```java
@Column(nullable = false)
private String name;

@Column(nullable = true)  // 기본값
private String phone;
```

**Python:**
```python
name = Column(String(100), nullable=False)  # NOT NULL
phone = Column(String(20), nullable=True)   # NULL 허용 (기본값)
```

**기본 동작**:
- `nullable` 생략 → `True` (NULL 허용)
- `primary_key=True` → 자동으로 `nullable=False`

---

### 2-5. unique (유일성 제약)

**Java:**
```java
@Column(unique = true)
private String email;
```

**Python:**
```python
email = Column(String(255), unique=True)
```

**실제 생성되는 SQL:**
```sql
CREATE TABLE users (
    email VARCHAR(255) UNIQUE
);
-- 또는
CREATE UNIQUE INDEX ix_users_email ON users (email);
```

---

### 2-6. index (인덱스 생성)

**Java:**
```java
@Column
@Index(name = "idx_phone")
private String phone;
```

**Python:**
```python
phone = Column(String(20), index=True)  # 자동으로 인덱스 생성
```

**생성되는 인덱스 이름**: `ix_{테이블명}_{컬럼명}`
```sql
CREATE INDEX ix_users_phone ON users (phone);
```

**unique + index 동시 사용:**
```python
email = Column(String(255), unique=True, index=True)
# ↓
# CREATE UNIQUE INDEX ix_users_email ON users (email);
```

---

### 2-7. default (기본값)

**Java:**
```java
@Column(columnDefinition = "BOOLEAN DEFAULT false")
private Boolean active = false;
```

**Python:**
```python
# 방법 1: Python 함수로 기본값 생성
id = Column(String(36), default=lambda: str(uuid.uuid4()))

# 방법 2: 고정 값
active = Column(Boolean, default=False)

# 방법 3: 현재 시간
created_at = Column(DateTime, default=datetime.now)
```

**default vs server_default:**

| 항목 | default | server_default |
|------|---------|----------------|
| 실행 위치 | **Python 코드** | **데이터베이스** |
| 사용 시점 | INSERT 전 | INSERT 시 |
| 예시 | `default=uuid.uuid4` | `server_default=func.now()` |

---

### 2-8. server_default (DB 기본값)

**Java:**
```java
@Column(columnDefinition = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
private LocalDateTime createdAt;
```

**Python:**
```python
from sqlalchemy.sql import func

created_at = Column(DateTime, server_default=func.now())
# ↓ SQL
# created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**문자열 기본값:**
```python
status = Column(String(20), server_default="ACTIVE")
# ↓ SQL
# status VARCHAR(20) DEFAULT 'ACTIVE'
```

---

### 2-9. onupdate (업데이트 시 자동 갱신)

**Java (JPA Auditing):**
```java
@LastModifiedDate
private LocalDateTime updatedAt;
```

**Python:**
```python
updated_at = Column(
    DateTime,
    server_default=func.now(),
    onupdate=func.now()  # ← UPDATE 시 자동 갱신
)
# ↓ SQL (MySQL)
# updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
```

**동작 방식:**
```python
user = User(name="John")
db.add(user)
db.commit()  # created_at = NOW(), updated_at = NOW()

user.name = "Jane"
db.commit()  # updated_at = NOW() (자동 갱신)
```

---

### 2-10. autoincrement (자동 증가)

**Java:**
```java
@Id
@GeneratedValue(strategy = GenerationType.IDENTITY)
private Long id;
```

**Python:**
```python
# 방법 1: 정수 PK (자동 증가)
id = Column(Integer, primary_key=True, autoincrement=True)

# 방법 2: UUID (자동 생성)
id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
```

**autoincrement 옵션:**

| 값 | 의미 |
|----|------|
| `"auto"` | 기본값. 단일 정수 PK면 자동 증가 |
| `True` | 강제로 자동 증가 활성화 |
| `False` | 자동 증가 비활성화 |
| `"ignore_fk"` | FK여도 자동 증가 (특수 케이스) |

---

## 3. 실전 예제

### 예제 1: User 테이블

```python
class User(Base):
    __tablename__ = "users"

    # UUID 기본 키
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # 필수 필드
    name = Column(String(100), nullable=False)

    # 유일 필드 + 인덱스
    phone = Column(String(20), unique=True, index=True)

    # 기본값 있는 필드
    alarm_enabled = Column(Boolean, nullable=False, default=False)

    # 자동 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
```

**생성되는 SQL:**
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE,
    alarm_enabled BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
CREATE INDEX ix_users_phone ON users (phone);
```

---

### 예제 2: 전화번호 인증 테이블

```python
class AuthPhoneVerification(Base):
    __tablename__ = "auth_phone_verifications"

    # 자동 증가 정수 ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Enum 컬럼
    purpose = Column(Enum(PhoneVerificationPurpose), nullable=False, index=True)

    # 일반 문자열
    phone = Column(String(20), nullable=False, index=True)

    # 해시된 코드
    code_hash = Column(String(100), nullable=False)

    # 상태 Enum
    status = Column(
        Enum(PhoneVerificationStatus),
        nullable=False,
        default=PhoneVerificationStatus.PENDING
    )

    # 만료 시간
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # 시도 횟수 (기본값 0)
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")
```

---

## 4. Java JPA vs SQLAlchemy 비교표

| 기능 | Java JPA | SQLAlchemy |
|------|----------|------------|
| 컬럼 정의 | `@Column` | `Column(...)` |
| 기본 키 | `@Id` | `primary_key=True` |
| 자동 증가 | `@GeneratedValue` | `autoincrement=True` |
| NULL 허용 | `nullable=false` | `nullable=False` |
| 유일성 | `unique=true` | `unique=True` |
| 기본값 | `columnDefinition` | `default` / `server_default` |
| 업데이트 시 갱신 | `@LastModifiedDate` | `onupdate=func.now()` |
| 인덱스 | `@Index` | `index=True` |
| Enum | `@Enumerated` | `Enum(MyEnum)` |

---

## 핵심 정리

1. **Column 클래스 = JPA @Column 어노테이션**
2. **type_ 파라미터로 데이터 타입 지정** (String, Integer, DateTime 등)
3. **nullable=False → NOT NULL 제약**
4. **unique=True → UNIQUE 제약**
5. **index=True → 인덱스 자동 생성**
6. **default → Python 기본값, server_default → DB 기본값**
7. **onupdate → UPDATE 시 자동 갱신**
8. **primary_key=True → 기본 키**
