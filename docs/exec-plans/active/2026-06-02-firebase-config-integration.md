# Firebase Config Integration Plan

**Date**: 2026-06-02  
**Status**: PLANNED  
**Priority**: HIGH (보안 이슈 포함)

---

## 배경 및 문제 정의

현재 상태:
- `config.py`에 `fcm_credentials_path: Optional[str] = None` 필드는 존재
- `FCMService.__init__`는 `credentials_path`를 받아 Firebase SDK를 초기화함
- **그러나 두 요소를 연결하는 코드가 없음** — `FCMService`가 `settings`를 읽지 않음
- `orderrun-firebase-key.json`이 프로젝트 루트에 존재하며 `.gitignore`에 없음 → **private key 노출 위험**

---

## 보안 우선: 즉시 처리 항목

### [0] Firebase 키 파일 gitignore 추가 (즉시 실행)

`orderrun-firebase-key.json`이 `git status`에 `??`(untracked)로 표시되어 있어 아직 커밋되지 않았지만,
즉시 `.gitignore`에 추가해야 함.

```
# .gitignore에 추가
orderrun-firebase-key.json
secrets/
```

---

## Firebase 키 파일 위치 결정

### 옵션 비교

| 방식 | 장점 | 단점 | 권장 환경 |
|------|------|------|----------|
| **A. 프로젝트 루트** (현재) | 편리 | git 실수로 커밋 위험, 경로 관리 어려움 | ❌ 사용 금지 |
| **B. `secrets/` 디렉토리** | 로컬에서 명확한 위치 | 배포 시 파일 복사 필요 | ✅ 로컬 개발용 |
| **C. 환경변수 (JSON 문자열)** | 파일 불필요, 배포 친화적 | env 길이 제한 주의 | ✅ 배포(staging/prod) |
| **D. `FCM_CREDENTIALS_JSON` + `FCM_CREDENTIALS_PATH` 병행** | 두 환경 모두 지원 | 설정 옵션이 늘어남 | ✅ **최종 선택** |

### 결정: 듀얼 방식 채택

```
로컬 개발   → secrets/orderrun-firebase-key.json (gitignored)
                FCM_CREDENTIALS_PATH=secrets/orderrun-firebase-key.json

Staging/Prod → FCM_CREDENTIALS_JSON='{...}' (GitHub Secret에 저장)
                앱 시작 시 JSON 문자열을 파싱하여 직접 credentials 생성
```

---

## 구현 계획

### Step 1: `.gitignore` 업데이트

- `orderrun-firebase-key.json` 추가
- `secrets/` 디렉토리 추가

### Step 2: `app/core/config.py` 수정

```python
# FCM 관련 설정을 두 가지 방식으로 지원
fcm_credentials_path: Optional[str] = None   # 로컬 파일 경로
fcm_credentials_json: Optional[str] = None   # JSON 문자열 (배포용)
```

### Step 3: `app/services/fcm_service.py` 수정

`FCMService.__init__`에서 `credentials_json` 문자열도 받을 수 있도록 수정:

```python
def __init__(
    self,
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None  # JSON 문자열
):
    # credentials_json이 있으면 파싱하여 Certificate 생성
    # credentials_path가 있으면 파일에서 로드
    # 둘 다 없으면 Application Default Credentials 시도
```

### Step 4: `app/core/firebase.py` 신규 생성 (싱글톤 팩토리)

`FCMService` 인스턴스를 애플리케이션 전체에서 공유하는 싱글톤 모듈:

```python
# app/core/firebase.py
from app.core.config import settings
from app.services.fcm_service import FCMService

_fcm_service: Optional[FCMService] = None

def get_fcm_service() -> FCMService:
    global _fcm_service
    if _fcm_service is None:
        _fcm_service = FCMService(
            credentials_path=settings.fcm_credentials_path,
            credentials_json=settings.fcm_credentials_json,
        )
    return _fcm_service
```

### Step 5: `app/main.py` startup 이벤트에서 초기화

앱 시작 시 FCM 연결 검증:

```python
@app.on_event("startup")
async def startup_event():
    # Firebase 초기화 (설정이 있을 때만)
    if settings.fcm_credentials_path or settings.fcm_credentials_json:
        fcm = get_fcm_service()
        if not fcm.initialized:
            logger.warning("FCM service failed to initialize")
```

### Step 6: `notification_dispatcher.py` 수정

기존에 `FCMService`를 직접 인스턴스화하는 코드가 있다면 `get_fcm_service()`로 교체.

### Step 7: `.env.example` 업데이트

```bash
# Firebase Cloud Messaging (FCM)
# 로컬 개발: 파일 경로 사용
FCM_CREDENTIALS_PATH=secrets/orderrun-firebase-key.json

# 배포 환경: JSON 문자열 사용 (GitHub Secret)
# FCM_CREDENTIALS_JSON={"type":"service_account",...}
```

### Step 8: `secrets/` 디렉토리 구성

```
secrets/
├── .gitkeep          # 디렉토리 추적용
└── README.md         # 로컬 개발 가이드
```

---

## 배포 환경(staging) 처리 방법

GitHub Actions workflow에서:

```yaml
- name: Set FCM credentials
  run: echo "FCM_CREDENTIALS_JSON=${{ secrets.FCM_CREDENTIALS_JSON }}" >> .env
```

GitHub Repository Secrets에 `FCM_CREDENTIALS_JSON` 키로 JSON 전체 내용 저장.

---

## 검증 기준

- [ ] `orderrun-firebase-key.json`이 `.gitignore`에 포함되어 있음
- [ ] `git status`에서 `orderrun-firebase-key.json`이 untracked으로 나오지 않음
- [ ] `FCM_CREDENTIALS_PATH`로 로컬 초기화 성공
- [ ] `FCM_CREDENTIALS_JSON`으로 파일 없이 초기화 성공
- [ ] `FCMService`가 `settings`와 연결됨 (직접 인스턴스화 없음)
- [ ] 둘 다 없을 때 앱이 정상 시작 (FCM 비활성 상태로)
- [ ] `.env.example`에 두 방식 모두 문서화됨

---

## 파일 변경 목록

| 파일 | 변경 유형 | 내용 |
|------|----------|------|
| `.gitignore` | 수정 | Firebase 키 파일 추가 |
| `app/core/config.py` | 수정 | `fcm_credentials_json` 필드 추가 |
| `app/core/firebase.py` | 신규 생성 | FCMService 싱글톤 팩토리 |
| `app/services/fcm_service.py` | 수정 | `credentials_json` 지원 추가 |
| `app/services/notification_dispatcher.py` | 수정 | 싱글톤 사용으로 교체 |
| `app/main.py` | 수정 | startup 이벤트에서 FCM 초기화 |
| `.env.example` | 수정 | FCM 설정 가이드 추가 |
| `secrets/README.md` | 신규 생성 | 로컬 키 파일 사용 가이드 |
