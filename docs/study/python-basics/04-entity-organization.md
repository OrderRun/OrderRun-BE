# 한 파일에 여러 엔티티를 관리하는 이유

> Java vs Python 프로젝트 구조 비교

## 1. Java/Spring의 전통적 구조

### Java의 파일 구조

**Java는 "한 파일 = 한 public 클래스" 규칙:**
```
models/
├── User.java                  # public class User
├── UserRepository.java        # public class UserRepository
├── AuthPhoneVerification.java # public class AuthPhoneVerification
├── PhoneVerificationPurpose.java  # public enum PhoneVerificationPurpose
└── PhoneVerificationStatus.java   # public enum PhoneVerificationStatus
```

**이유:**
- Java 컴파일러 제약: **한 파일에 하나의 public 클래스만 허용**
- 클래스명과 파일명이 일치해야 함 (`User.java` → `public class User`)

---

## 2. Python의 유연한 구조

### Python은 한 파일에 여러 클래스 가능

**Python의 파일 구조:**
```
models/
└── user.py                    # User, AuthPhoneVerification, Enum 등 모두 포함
```

**user.py 내부:**
```python
# 한 파일에 여러 클래스 정의 가능
class PhoneVerificationPurpose(str, enum.Enum):
    SIGNUP = "SIGNUP"
    LOGIN = "LOGIN"

class PhoneVerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"

class User(Base):
    __tablename__ = "users"
    # ...

class AuthPhoneVerification(Base):
    __tablename__ = "auth_phone_verifications"
    # ...

class UserFCMToken(Base):
    __tablename__ = "user_fcm_tokens"
    # ...
```

**이유:**
- Python은 **파일명과 클래스명이 무관**
- **한 파일 = 한 모듈** (여러 클래스 포함 가능)
- 관련된 클래스를 응집도 높게 묶을 수 있음

---

## 3. 왜 user.py에 여러 엔티티를 두는가?

### 이유 1: 도메인 응집도 (Domain Cohesion)

**관련 있는 클래스를 한 곳에 모음:**

```python
# user.py: User 도메인 관련 모든 것
- User                         # 사용자 엔티티
- AuthPhoneVerification        # 전화번호 인증 (User와 밀접)
- UserFCMToken                 # User의 FCM 토큰
- PhoneVerificationPurpose     # 인증 목적 Enum (SIGNUP, LOGIN)
- PhoneVerificationStatus      # 인증 상태 Enum (PENDING, VERIFIED)
```

**장점:**
- User 관련 코드를 **한 파일**에서 관리 가능
- import 간소화: `from app.models.user import User, AuthPhoneVerification`

---

### 이유 2: 순환 참조 방지

**Java의 순환 참조 문제:**
```java
// User.java
import models.AuthPhoneVerification;  // ← AuthPhoneVerification 참조

public class User {
    // ...
}

// AuthPhoneVerification.java
import models.User;  // ← User 참조

public class AuthPhoneVerification {
    // ...
}
```
- 서로 참조하지만 Java는 이를 허용 (같은 컴파일 단위)

**Python의 해결책: 한 파일에 두면 순환 참조 문제 없음**
```python
# user.py
class User(Base):
    # AuthPhoneVerification와 관계 맺음
    pass

class AuthPhoneVerification(Base):
    # User와 관계 맺음
    pass

# ✅ 같은 파일이므로 순환 참조 걱정 없음
```

---

### 이유 3: import 편의성

**Java (여러 파일):**
```java
import models.User;
import models.AuthPhoneVerification;
import models.PhoneVerificationPurpose;
import models.PhoneVerificationStatus;
import models.UserFCMToken;
```

**Python (한 파일):**
```python
from app.models.user import (
    User,
    AuthPhoneVerification,
    PhoneVerificationPurpose,
    PhoneVerificationStatus,
    UserFCMToken,
)
```
- 한 줄로 모든 User 관련 클래스 import 가능

---

### 이유 4: 작은 클래스들의 관리

**Enum이나 작은 클래스는 별도 파일로 나누면 번거로움:**

**만약 Java처럼 분리한다면:**
```
models/
├── user.py                           # User만
├── auth_phone_verification.py        # AuthPhoneVerification만
├── user_fcm_token.py                 # UserFCMToken만
├── phone_verification_purpose.py     # Enum만
└── phone_verification_status.py      # Enum만
```
- 파일이 너무 많아짐 (Enum 하나에 파일 하나)
- 관련 코드가 흩어짐

**Python의 접근:**
```
models/
└── user.py  # User 도메인 전체
```
- 응집도 높은 구조
- 파일 수 감소

---

## 4. 실제 프로젝트 비교

### Spring Boot 프로젝트 (Java)

```
com.orderrun.models/
├── user/
│   ├── User.java
│   ├── UserRepository.java
│   ├── AuthPhoneVerification.java
│   ├── AuthPhoneVerificationRepository.java
│   ├── UserFCMToken.java
│   ├── PhoneVerificationPurpose.java
│   └── PhoneVerificationStatus.java
├── proposal/
│   ├── Proposal.java
│   ├── ProposalRepository.java
│   └── ProposalStatus.java
└── offer/
    ├── Offer.java
    ├── OfferRepository.java
    └── OfferStatus.java
```

---

### FastAPI 프로젝트 (Python)

```
app/models/
├── user.py          # User, AuthPhoneVerification, UserFCMToken, Enums
├── proposal.py      # Proposal, ProposalStatus
└── offer.py         # Offer, OfferStatus
```

---

## 5. 언제 파일을 분리하는가?

### 분리가 필요한 경우

**1. 파일이 너무 커질 때 (500줄 이상)**
```python
# user.py가 1000줄이면 분리 고려
user.py → user_auth.py + user_profile.py + user_fcm.py
```

**2. 독립적인 도메인일 때**
```python
# User와 Proposal은 독립적
user.py      # User 도메인
proposal.py  # Proposal 도메인
```

**3. 순환 참조 문제가 발생할 때**
```python
# user.py가 proposal.py를 import하고
# proposal.py가 user.py를 import하면 → 분리 필요
```

---

### 함께 두는 것이 좋은 경우

**1. 밀접하게 관련된 클래스**
```python
# user.py
class User(Base):
    pass

class UserFCMToken(Base):  # User의 종속 엔티티
    user_id = Column(String(36), ForeignKey("users.id"))
```

**2. 작은 Enum/상수 클래스**
```python
# user.py
class PhoneVerificationPurpose(str, enum.Enum):
    SIGNUP = "SIGNUP"
    LOGIN = "LOGIN"
```

**3. 함께 사용되는 클래스**
```python
# user.py
class User(Base):
    pass

class AuthPhoneVerification(Base):  # User 인증에만 사용
    pass
```

---

## 6. Python vs Java 철학 비교

| 측면 | Java | Python |
|------|------|--------|
| **파일 구조** | 한 파일 = 한 클래스 (강제) | 한 파일 = 여러 클래스 (자유) |
| **파일명** | 클래스명과 일치 필수 | 클래스명과 무관 |
| **모듈** | 패키지(디렉토리) | 파일 = 모듈 |
| **응집도** | 디렉토리로 묶음 | 파일로 묶음 |
| **철학** | "명시적 분리" | "실용적 응집" |

---

## 7. OrderRun-BE의 실제 구조

### 현재 구조

```python
app/models/
├── user.py          # User, AuthPhoneVerification, UserFCMToken, Enums
├── proposal.py      # Proposal 도메인
├── offer.py         # Offer 도메인
├── mission.py       # Mission 도메인
├── payment.py       # Payment 도메인
├── notification.py  # Notification 도메인
└── terms.py         # Terms 도메인
```

**왜 이렇게 나눴는가?**
1. **도메인별 분리**: User, Proposal, Offer 등은 독립적
2. **파일 크기 관리**: 각 파일 200~300줄 유지
3. **import 편의성**: 도메인별로 한 번에 import 가능

---

## 8. 실전 조언

### ✅ 좋은 예

**관련 엔티티를 한 파일에:**
```python
# user.py
class User(Base):
    pass

class UserProfile(Base):  # User의 프로필
    user_id = Column(ForeignKey("users.id"))

class UserSettings(Base):  # User의 설정
    user_id = Column(ForeignKey("users.id"))
```

---

### ❌ 나쁜 예

**무관한 엔티티를 한 파일에:**
```python
# models.py (모든 엔티티를 한 파일에)
class User(Base):
    pass

class Proposal(Base):  # User와 독립적 → 분리해야 함
    pass

class Offer(Base):  # Proposal과 독립적 → 분리해야 함
    pass
```

---

## 핵심 정리

1. **Java**: 컴파일러 제약으로 한 파일 = 한 클래스
2. **Python**: 자유도가 높아 한 파일 = 여러 클래스 가능
3. **응집도**: 관련된 클래스를 한 파일에 묶어 관리
4. **편의성**: import 간소화, 순환 참조 방지
5. **분리 기준**:
   - 파일이 커지면 분리
   - 독립적 도메인이면 분리
   - 밀접한 관계면 유지
