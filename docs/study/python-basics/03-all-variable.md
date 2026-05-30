# Python __all__ 변수 가이드

> Java의 public/private 접근 제어와 비교하여 설명

## __all__ 변수란?

`__all__`은 **모듈에서 공개할 이름(클래스, 함수, 변수)을 명시**하는 특별한 리스트 변수입니다.

---

## 1. Java와 비교

### Java의 접근 제어

**Java:**
```java
// User.java
package com.example.models;

public class User { }           // ✅ 외부에서 접근 가능
public class UserRepository { } // ✅ 외부에서 접근 가능
class InternalHelper { }        // ❌ 패키지 내부에서만 사용
```

**Python:**
```python
# user.py
class User:
    pass

class UserRepository:
    pass

class _InternalHelper:  # ← 관례상 private (언더스코어)
    pass

# 공개할 것만 명시
__all__ = ["User", "UserRepository"]
```

---

## 2. __all__의 역할

### 역할 1: from module import * 제어

**Python 파일 구조:**
```python
# models/user.py
class User:
    pass

class AuthPhoneVerification:
    pass

class PhoneVerificationPurpose:
    pass

class _InternalHelper:  # 내부 전용
    pass

# 공개할 것만 명시
__all__ = [
    "User",
    "AuthPhoneVerification",
    "PhoneVerificationPurpose",
]
```

**다른 파일에서 import:**
```python
# 방법 1: * 사용 (권장하지 않음, 하지만 __all__로 제어 가능)
from models.user import *

# ✅ 사용 가능
user = User()
verification = AuthPhoneVerification()

# ❌ 사용 불가 (_InternalHelper는 __all__에 없음)
helper = _InternalHelper()  # NameError

# 방법 2: 명시적 import (권장)
from models.user import User, AuthPhoneVerification
```

---

### 역할 2: 문서화 및 IDE 자동완성

**__all__이 있으면:**
- IDE가 자동완성 시 공개된 항목만 표시
- 코드 리뷰 시 "이 모듈에서 공개하는 것"을 명확히 알 수 있음

**예시 (VSCode, PyCharm):**
```python
from models.user import [Tab]  # 자동완성
# ↓ __all__에 있는 것만 제안
# User, AuthPhoneVerification, PhoneVerificationPurpose
```

---

## 3. user.py의 실제 __all__ 분석

```python
# app/models/user.py 마지막 부분
__all__ = [
    "AuthPhoneVerification",
    "PhoneVerificationPurpose",
    "PhoneVerificationStatus",
    "User",
    "UserFCMToken",
]
```

**의미:**
1. 이 모듈은 5개 항목을 공개합니다.
2. `from app.models.user import *` 사용 시 이 5개만 가져옵니다.
3. 다른 내부 헬퍼 함수/클래스가 있어도 공개되지 않습니다.

---

## 4. __all__ 사용 시점

### 사용하는 경우

**1. 공개 API가 명확한 라이브러리/모듈**
```python
# models/user.py
__all__ = ["User", "UserRepository"]  # 공개 API 명시
```

**2. from module import * 사용을 제어하고 싶을 때**
```python
# utils.py
def public_helper():
    pass

def _private_helper():
    pass

__all__ = ["public_helper"]  # * 사용 시 public_helper만 가져옴
```

**3. 모듈이 제공하는 기능을 문서화하고 싶을 때**
```python
# api.py
"""
이 모듈은 User 관련 API를 제공합니다.
"""
__all__ = ["create_user", "get_user", "update_user", "delete_user"]
```

---

### 사용하지 않는 경우

**1. 명시적 import만 사용하는 프로젝트**
```python
# 명시적 import (권장)
from models.user import User, AuthPhoneVerification

# __all__ 없어도 문제없음
```

**2. 모든 것이 공개되어야 하는 경우**
```python
# constants.py
MAX_SIZE = 100
MIN_SIZE = 10
DEFAULT_SIZE = 50

# __all__ 불필요 (모두 공개)
```

---

## 5. __all__ vs 언더스코어(_) 관례

### Python의 private 관례

**Java:**
```java
public class User {
    private String password;  // private 키워드
}
```

**Python:**
```python
class User:
    def __init__(self):
        self._password = "secret"  # ← 언더스코어 = private 관례
        self.name = "John"         # ← 언더스코어 없음 = public
```

**차이점:**

| 방법 | Java 비교 | 강제성 | 용도 |
|------|-----------|--------|------|
| `_name` | `private` | ❌ 관례만, 접근 가능 | 내부 전용 표시 |
| `__all__` | `public API` | ✅ `import *` 제어 | 공개 API 명시 |

**예시:**
```python
class User:
    def __init__(self):
        self.name = "John"      # public
        self._password = "123"  # private (관례)

    def _internal_method(self):  # private 메서드 (관례)
        pass

    def public_method(self):     # public 메서드
        pass

# 하지만 실제로는 접근 가능 (Python의 철학: "We're all consenting adults")
user = User()
print(user._password)  # "123" (접근 가능, 하지만 하지 말아야 함)
```

---

## 6. 실전 예제

### 예제 1: 모델 모듈

```python
# models/user.py
class User:
    pass

class UserRepository:
    pass

class _UserCache:  # 내부 전용
    pass

def _validate_user(user):  # 내부 전용
    pass

__all__ = ["User", "UserRepository"]
```

**사용:**
```python
# main.py
from models.user import *

user = User()         # ✅
repo = UserRepository()  # ✅
cache = _UserCache()  # ❌ NameError (또는 IDE가 경고)
```

---

### 예제 2: API 라우터 모듈

```python
# api/users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
def list_users():
    pass

@router.post("/users")
def create_user():
    pass

def _validate_email(email: str):  # 내부 헬퍼
    pass

__all__ = ["router"]  # router만 공개
```

**사용:**
```python
# main.py
from api.users import router  # 명시적 import (권장)

# 또는
from api.users import *
app.include_router(router)  # ✅ router만 가져옴
```

---

## 7. 모범 사례 (Best Practices)

### ✅ 좋은 예

**1. 공개 API가 명확한 모듈**
```python
# services/auth.py
__all__ = ["AuthService", "TokenService"]
```

**2. 라이브러리 패키지의 __init__.py**
```python
# mylib/__init__.py
from .user import User
from .auth import AuthService

__all__ = ["User", "AuthService"]
```

---

### ❌ 나쁜 예

**1. __all__에 없는데 public인 것처럼 이름 짓기**
```python
class PublicClass:  # public처럼 보이지만
    pass

__all__ = []  # __all__에 없음 (혼란)
```

**2. __all__과 실제 정의가 불일치**
```python
class User:
    pass

__all__ = ["User", "UserRepository"]  # ❌ UserRepository는 정의 안 됨
```

---

## 8. Java와의 최종 비교

| 개념 | Java | Python |
|------|------|--------|
| **public 클래스** | `public class User` | `class User` + `__all__` |
| **private 클래스** | `class Helper` (패키지 전용) | `class _Helper` (관례) |
| **public 메서드** | `public void method()` | `def method()` |
| **private 메서드** | `private void method()` | `def _method()` (관례) |
| **API 명시** | 인터페이스 또는 문서 | `__all__` |
| **접근 제어 강제** | ✅ 컴파일러 | ❌ 관례 + 도구 |

---

## 핵심 정리

1. **__all__**: 모듈에서 공개할 항목 리스트
2. **from module import * 제어**: __all__에 있는 것만 가져옴
3. **문서화**: 이 모듈이 제공하는 공개 API 명시
4. **IDE 지원**: 자동완성 시 __all__ 항목만 제안
5. **언더스코어(_) 관례**: private 표시 (강제 아님)
6. **모범 사례**: 공개 API가 명확한 모듈에만 사용
