# SQLAlchemy relationship 완벽 가이드

> Java JPA @OneToMany, @ManyToOne과 비교하여 설명

## relationship 개요

SQLAlchemy의 `relationship`은 **엔티티 간의 관계**를 정의하는 함수입니다.
**Java JPA의 `@OneToMany`, `@ManyToOne`, `@ManyToMany`와 동일한 역할**을 합니다.

---

## 1. 기본 개념

### Java JPA와 비교

**Java JPA (1:N 관계):**
```java
@Entity
public class User {
    @Id
    private String id;

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<DeviceToken> deviceTokens;
}

@Entity
public class DeviceToken {
    @Id
    private Long id;

    @ManyToOne
    @JoinColumn(name = "user_id")
    private User user;
}
```

**SQLAlchemy (1:N 관계):**
```python
class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)

    # 관계 정의 (FK는 상대 테이블에 있음)
    device_tokens = relationship(
        "DeviceToken",              # 상대 클래스명
        back_populates="user",      # 상대 필드명
        cascade="all, delete-orphan"  # 연쇄 삭제
    )

class DeviceToken(Base):
    __tablename__ = "device_tokens"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"))  # FK

    # 역방향 관계
    user = relationship("User", back_populates="device_tokens")
```

---

## 2. relationship 파라미터

### 2-1. 첫 번째 인자: 상대 클래스명

```python
device_tokens = relationship("DeviceToken")
#                           ↑ 상대 클래스명 (문자열)
```

**왜 문자열인가?**
- Python에서 클래스가 아직 정의되지 않았을 수 있음 (순환 참조 방지)
- 런타임에 SQLAlchemy가 자동으로 클래스 객체를 찾음

**클래스 직접 사용도 가능:**
```python
device_tokens = relationship(DeviceToken)  # 클래스가 이미 정의된 경우
```

---

### 2-2. back_populates (양방향 관계)

**Java JPA:**
```java
// User.java
@OneToMany(mappedBy = "user")
private List<DeviceToken> deviceTokens;

// DeviceToken.java
@ManyToOne
@JoinColumn(name = "user_id")
private User user;
```

**SQLAlchemy:**
```python
# User
device_tokens = relationship("DeviceToken", back_populates="user")
#                                          ↑ DeviceToken의 필드명

# DeviceToken
user = relationship("User", back_populates="device_tokens")
#                          ↑ User의 필드명
```

**동작 원리:**
```python
user = User(name="John")
token = DeviceToken(token="abc123")

# 한쪽만 설정해도 양쪽 모두 연결됨
user.device_tokens.append(token)
print(token.user)  # <User name="John"> (자동 연결)
```

---

### 2-3. cascade (연쇄 작업)

**Java JPA:**
```java
@OneToMany(
    mappedBy = "user",
    cascade = {CascadeType.PERSIST, CascadeType.REMOVE},
    orphanRemoval = true
)
private List<DeviceToken> deviceTokens;
```

**SQLAlchemy:**
```python
device_tokens = relationship(
    "DeviceToken",
    cascade="all, delete-orphan"  # 모든 작업 + 고아 객체 삭제
)
```

**cascade 옵션:**

| SQLAlchemy | JPA | 설명 |
|------------|-----|------|
| `"all"` | `CascadeType.ALL` | 모든 작업 전파 |
| `"save-update"` | `CascadeType.PERSIST` | 저장/업데이트 전파 |
| `"delete"` | `CascadeType.REMOVE` | 삭제 전파 |
| `"delete-orphan"` | `orphanRemoval=true` | 부모와 연결 끊어진 자식 삭제 |
| `"merge"` | `CascadeType.MERGE` | 병합 전파 |
| `"refresh"` | `CascadeType.REFRESH` | 새로고침 전파 |

**예시:**
```python
user = User(name="John")
token1 = DeviceToken(token="abc")
token2 = DeviceToken(token="def")
user.device_tokens = [token1, token2]

db.add(user)
db.commit()  # user, token1, token2 모두 저장 (cascade)

db.delete(user)
db.commit()  # user 삭제 시 token1, token2도 삭제 (cascade="delete")
```

---

### 2-4. uselist (단일 객체 vs 리스트)

**Java JPA:**
```java
// 1:N (리스트)
@OneToMany(mappedBy = "user")
private List<DeviceToken> deviceTokens;

// 1:1 (단일 객체)
@OneToOne(mappedBy = "user")
private NotificationPreference preference;
```

**SQLAlchemy:**
```python
# 1:N (리스트) - 기본값
device_tokens = relationship("DeviceToken")  # uselist=True (기본값)
# user.device_tokens → [token1, token2, ...]

# 1:1 (단일 객체)
notification_preference = relationship(
    "NotificationPreference",
    uselist=False  # ← 리스트가 아닌 단일 객체
)
# user.notification_preference → <NotificationPreference object>
```

---

### 2-5. lazy (지연 로딩 전략)

**Java JPA:**
```java
@OneToMany(mappedBy = "user", fetch = FetchType.LAZY)
private List<DeviceToken> deviceTokens;

@OneToMany(mappedBy = "user", fetch = FetchType.EAGER)
private List<Order> orders;
```

**SQLAlchemy:**
```python
# 기본값: lazy="select" (JPA의 LAZY와 동일)
device_tokens = relationship("DeviceToken", lazy="select")

# 즉시 로딩 (JPA의 EAGER)
orders = relationship("Order", lazy="joined")
```

**lazy 옵션:**

| SQLAlchemy | JPA | 설명 |
|------------|-----|------|
| `"select"` | `FetchType.LAZY` | 접근 시 별도 SELECT 쿼리 |
| `"joined"` | `FetchType.EAGER` | JOIN으로 함께 조회 |
| `"subquery"` | - | 서브쿼리로 조회 |
| `"dynamic"` | - | Query 객체 반환 (필터링 가능) |
| `True` | `FetchType.LAZY` | `"select"`와 동일 |
| `False` | `FetchType.EAGER` | `"joined"`와 동일 |

**예시:**
```python
# lazy="select" (기본값)
user = db.query(User).first()
# SELECT * FROM users WHERE id = 1

print(user.device_tokens)  # ← 이 순간 추가 쿼리 발생
# SELECT * FROM device_tokens WHERE user_id = '...'

# lazy="joined"
user = db.query(User).first()
# SELECT * FROM users
# LEFT JOIN device_tokens ON users.id = device_tokens.user_id
# WHERE users.id = 1
# (한 번에 조회)
```

---

## 3. 관계 유형별 예제

### 3-1. One-to-Many (1:N)

**시나리오**: 한 명의 User는 여러 개의 DeviceToken을 가질 수 있다.

```python
class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)

    device_tokens = relationship(
        "DeviceToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

class DeviceToken(Base):
    __tablename__ = "device_tokens"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"))
    token = Column(String(512), nullable=False)

    user = relationship("User", back_populates="device_tokens")
```

**사용법:**
```python
user = User(id="user-1")
token1 = DeviceToken(token="abc123")
token2 = DeviceToken(token="def456")

user.device_tokens.append(token1)
user.device_tokens.append(token2)

db.add(user)
db.commit()
```

---

### 3-2. One-to-One (1:1)

**시나리오**: 한 명의 User는 하나의 NotificationPreference를 가진다.

```python
class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)

    notification_preference = relationship(
        "NotificationPreference",
        back_populates="user",
        uselist=False,  # ← 1:1 관계
        cascade="all, delete-orphan"
    )

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True)
    email_enabled = Column(Boolean, default=True)

    user = relationship("User", back_populates="notification_preference")
```

**사용법:**
```python
user = User(id="user-1")
pref = NotificationPreference(email_enabled=True)

user.notification_preference = pref  # 단일 객체 할당

db.add(user)
db.commit()
```

---

### 3-3. Many-to-Many (N:M)

**시나리오**: User와 Role은 다대다 관계 (중간 테이블 필요)

```python
# 중간 테이블 (Association Table)
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String(36), ForeignKey('users.id')),
    Column('role_id', String(36), ForeignKey('roles.id'))
)

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)

    roles = relationship(
        "Role",
        secondary=user_roles,  # ← 중간 테이블
        back_populates="users"
    )

class Role(Base):
    __tablename__ = "roles"
    id = Column(String(36), primary_key=True)
    name = Column(String(50), nullable=False)

    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )
```

**사용법:**
```python
user = User(id="user-1")
role_admin = Role(name="ADMIN")
role_user = Role(name="USER")

user.roles.append(role_admin)
user.roles.append(role_user)

db.add(user)
db.commit()
```

---

## 4. user.py의 실제 relationship 분석

```python
class User(Base):
    __tablename__ = "users"

    # 1:N 관계 - DeviceToken
    device_tokens = relationship(
        "DeviceToken",              # 상대 클래스
        back_populates="user",      # 양방향 연결
        cascade="all, delete-orphan"  # User 삭제 시 DeviceToken도 삭제
    )

    # 1:N 관계 - Notification
    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # 1:1 관계 - NotificationPreference
    notification_preference = relationship(
        "NotificationPreference",
        back_populates="user",
        uselist=False,              # ← 단일 객체
        cascade="all, delete-orphan"
    )
```

**동작 예시:**
```python
# User 삭제 시 연쇄 삭제
user = db.query(User).filter(User.id == "user-1").first()
db.delete(user)
db.commit()
# ↓
# DELETE FROM device_tokens WHERE user_id = 'user-1'
# DELETE FROM notifications WHERE user_id = 'user-1'
# DELETE FROM notification_preferences WHERE user_id = 'user-1'
# DELETE FROM users WHERE id = 'user-1'
```

---

## 5. Java JPA vs SQLAlchemy 비교표

| 기능 | Java JPA | SQLAlchemy |
|------|----------|------------|
| 1:N 관계 | `@OneToMany` | `relationship(...)` |
| N:1 관계 | `@ManyToOne` | `relationship(...) + ForeignKey` |
| 1:1 관계 | `@OneToOne` | `relationship(..., uselist=False)` |
| N:M 관계 | `@ManyToMany` | `relationship(..., secondary=...)` |
| 양방향 | `mappedBy="..."` | `back_populates="..."` |
| 연쇄 작업 | `cascade=CascadeType.ALL` | `cascade="all"` |
| 고아 삭제 | `orphanRemoval=true` | `cascade="delete-orphan"` |
| 지연 로딩 | `fetch=FetchType.LAZY` | `lazy="select"` |
| 즉시 로딩 | `fetch=FetchType.EAGER` | `lazy="joined"` |

---

## 핵심 정리

1. **relationship = JPA의 @OneToMany, @ManyToOne 등**
2. **back_populates = 양방향 관계 설정** (JPA의 mappedBy)
3. **cascade = 연쇄 작업 전파** (저장, 삭제 등)
4. **uselist=False = 1:1 관계** (기본은 1:N)
5. **lazy = 지연 로딩 전략** (select, joined 등)
6. **ForeignKey는 Column에 정의**, relationship은 관계만 정의
