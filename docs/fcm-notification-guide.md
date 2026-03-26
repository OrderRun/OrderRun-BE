# FCM Notification System Guide

## 개요

OrderRun 앱의 FCM (Firebase Cloud Messaging) 알림 시스템은 사용자에게 실시간 푸시 알림을 전송할 수 있는 공통 모듈입니다. 이 시스템은 비즈니스 이벤트가 발생할 때 어떤 API에서든 알림을 보낼 수 있도록 설계되었습니다.

## 아키텍처

### 핵심 컴포넌트

1. **Models** (`app/models/notification.py`)
   - `DeviceToken`: FCM 디바이스 토큰 관리
   - `Notification`: 알림 기록 저장
   - `NotificationPreference`: 사용자별 알림 설정

2. **Schemas** (`app/schemas/notification.py`)
   - Pydantic 모델을 통한 요청/응답 검증
   - FCM 페이로드 스키마

3. **FCM Service** (`app/services/fcm_service.py`)
   - Firebase Admin SDK를 사용한 실제 알림 전송
   - 단일/다중 디바이스 전송 지원
   - 토픽 기반 브로드캐스트 지원

4. **Notification Dispatcher** (`app/services/notification_dispatcher.py`)
   - 비즈니스 이벤트를 알림으로 변환
   - 사용자 설정 확인 및 필터링
   - 모든 API에서 사용 가능한 중앙 집중식 디스패처

5. **API Endpoints** (`app/api/v1/notifications.py`)
   - 디바이스 토큰 등록/관리
   - 알림 목록 조회
   - 알림 설정 관리

## 설치 및 설정

### 1. Firebase Admin SDK 설치

```bash
pip install firebase-admin
```

또는 `pyproject.toml`에 추가:

```toml
[project]
dependencies = [
    "firebase-admin>=6.0.0",
    # ... other dependencies
]
```

### 2. Firebase 서비스 계정 키 생성

1. Firebase Console (https://console.firebase.google.com/) 접속
2. 프로젝트 선택 또는 새 프로젝트 생성
3. 프로젝트 설정 > 서비스 계정
4. "새 비공개 키 생성" 클릭
5. JSON 파일 다운로드

### 3. 서비스 계정 키 파일 저장

```bash
mkdir -p keys
mv ~/Downloads/firebase-service-account-*.json keys/firebase-service-account.json
```

`.gitignore`에 추가되어 있는지 확인:
```
keys/
*.json
```

### 4. 환경 변수 설정

`.env` 파일에 추가:
```bash
FCM_CREDENTIALS_PATH=./keys/firebase-service-account.json
```

### 5. 데이터베이스 마이그레이션

알림 관련 테이블을 생성합니다:

```bash
# Alembic을 사용하는 경우
alembic revision --autogenerate -m "Add notification tables"
alembic upgrade head

# 또는 직접 테이블 생성
python -c "from app.core.database import engine, Base; from app.models.notification import *; Base.metadata.create_all(bind=engine)"
```

## 사용 방법

### 1. 디바이스 토큰 등록 (클라이언트 측)

클라이언트 앱에서 FCM 토큰을 받아 서버에 등록합니다.

**API 요청:**
```http
POST /api/v1/notifications/device-tokens
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "token": "fcm-device-token-here",
  "platform": "ios",  // "ios", "android", or "web"
  "device_id": "iPhone14,3"  // Optional
}
```

**응답:**
```json
{
  "id": 1,
  "user_id": 123,
  "token": "fcm-device-token-here",
  "platform": "ios",
  "device_id": "iPhone14,3",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "last_used_at": null
}
```

### 2. 비즈니스 로직에서 알림 보내기

#### 방법 1: Notification Dispatcher 사용 (권장)

가장 간단하고 권장되는 방법입니다. 디스패처가 모든 복잡한 로직을 처리합니다.

```python
from sqlalchemy.orm import Session
from app.services.fcm_service import FCMService
from app.services.notification_dispatcher import NotificationDispatcher
from app.core.config import settings

# 디스패처 초기화
fcm_service = FCMService(credentials_path=settings.fcm_credentials_path)
dispatcher = NotificationDispatcher(fcm_service)

# 예시 1: 의뢰가 매칭되었을 때
def match_proposal(db: Session, proposal_id: int, customer_id: int, runner_id: int):
    # ... 비즈니스 로직 ...

    # 알림 전송
    dispatcher.notify_proposal_matched(
        db=db,
        proposal_id=proposal_id,
        customer_id=customer_id,
        runner_id=runner_id,
        proposal_title="강남역에서 홍대입구까지 배달"
    )

    return {"status": "matched"}

# 예시 2: 새로운 제안을 받았을 때
def create_offer(db: Session, offer_data: dict):
    # ... 비즈니스 로직 ...

    # 알림 전송
    dispatcher.notify_offer_received(
        db=db,
        offer_id=new_offer.id,
        proposal_id=offer_data["proposal_id"],
        customer_id=proposal.customer_id,
        runner_id=current_user.id,
        proposal_title=proposal.title,
        offer_amount=offer_data["amount"]
    )

    return new_offer

# 예시 3: 결제가 완료되었을 때
def complete_payment(db: Session, payment_id: int):
    # ... 비즈니스 로직 ...

    # 알림 전송
    dispatcher.notify_payment_completed(
        db=db,
        payment_id=payment_id,
        user_id=payment.user_id,
        amount=payment.amount,
        mission_title=payment.mission.title
    )

    return {"status": "completed"}
```

#### 방법 2: FCM Service 직접 사용

더 세밀한 제어가 필요한 경우 FCM Service를 직접 사용할 수 있습니다.

```python
from app.services.fcm_service import FCMService
from app.models.notification import NotificationType

fcm_service = FCMService(credentials_path=settings.fcm_credentials_path)

# 특정 사용자에게 알림 전송
notification, results = fcm_service.send_to_user(
    db=db,
    user_id=123,
    notification_type=NotificationType.MISSION_COMPLETED,
    title="미션 완료!",
    body="강남역 배달 미션을 완료했습니다.",
    data={
        "mission_id": 456,
        "reward": "15000"
    },
    related_entity_type="mission",
    related_entity_id=456
)

print(f"Notification ID: {notification.id}")
print(f"Sent to {len(results)} devices")
```

### 3. FastAPI Dependency Injection 패턴

FastAPI 엔드포인트에서 의존성 주입을 통해 사용:

```python
from fastapi import APIRouter, Depends
from app.services.notification_dispatcher import NotificationDispatcher
from app.api.v1.notifications import get_notification_dispatcher

router = APIRouter()

@router.post("/proposals/{proposal_id}/accept")
def accept_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    dispatcher: NotificationDispatcher = Depends(get_notification_dispatcher)
):
    # 비즈니스 로직
    proposal = get_proposal(db, proposal_id)

    # 알림 전송
    dispatcher.notify_proposal_matched(
        db=db,
        proposal_id=proposal.id,
        customer_id=proposal.customer_id,
        runner_id=current_user.id,
        proposal_title=proposal.title
    )

    return {"status": "accepted"}
```

## 알림 타입

시스템에서 지원하는 알림 타입:

| 타입 | 설명 | 사용 시나리오 |
|------|------|---------------|
| `PROPOSAL_NEW` | 새 의뢰 생성 | 의뢰가 생성되었을 때 주변 러너에게 알림 |
| `PROPOSAL_MATCHED` | 의뢰 매칭 완료 | 의뢰와 제안이 매칭되었을 때 |
| `PROPOSAL_CANCELLED` | 의뢰 취소 | 의뢰가 취소되었을 때 |
| `OFFER_NEW` | 새 제안 도착 | 의뢰에 새로운 제안이 들어왔을 때 |
| `OFFER_ACCEPTED` | 제안 수락 | 러너의 제안이 수락되었을 때 |
| `OFFER_REJECTED` | 제안 거절 | 러너의 제안이 거절되었을 때 |
| `MISSION_STARTED` | 미션 시작 | 미션이 시작되었을 때 |
| `MISSION_COMPLETED` | 미션 완료 | 미션이 완료되었을 때 |
| `PAYMENT_COMPLETED` | 결제 완료 | 결제가 성공적으로 완료되었을 때 |
| `PAYMENT_FAILED` | 결제 실패 | 결제가 실패했을 때 |
| `SYSTEM_ANNOUNCEMENT` | 시스템 공지 | 전체 또는 특정 사용자에게 공지 |
| `CUSTOM` | 커스텀 알림 | 기타 커스텀 알림 |

## API 엔드포인트

### 디바이스 토큰 관리

```http
# 디바이스 토큰 등록
POST /api/v1/notifications/device-tokens

# 디바이스 토큰 목록 조회
GET /api/v1/notifications/device-tokens

# 디바이스 토큰 업데이트 (비활성화)
PATCH /api/v1/notifications/device-tokens/{token_id}

# 디바이스 토큰 삭제
DELETE /api/v1/notifications/device-tokens/{token_id}
```

### 알림 조회

```http
# 알림 목록 조회
GET /api/v1/notifications?page=1&page_size=20&unread_only=false

# 특정 알림 조회
GET /api/v1/notifications/{notification_id}

# 알림 읽음 처리
POST /api/v1/notifications/mark-read
{
  "notification_ids": [1, 2, 3]
}

# 알림 통계
GET /api/v1/notifications/stats/me
```

### 알림 설정

```http
# 알림 설정 조회
GET /api/v1/notifications/preferences/me

# 알림 설정 업데이트
PATCH /api/v1/notifications/preferences/me
{
  "enable_proposal_notifications": true,
  "enable_offer_notifications": true,
  "enable_mission_notifications": true,
  "enable_payment_notifications": true,
  "enable_system_notifications": false,
  "enable_quiet_hours": true,
  "quiet_hours_start": 22,
  "quiet_hours_end": 8
}
```

### 테스트용 알림 전송

```http
POST /api/v1/notifications/send
{
  "notification_type": "custom",
  "title": "테스트 알림",
  "body": "이것은 테스트 알림입니다.",
  "data": {
    "custom_field": "custom_value"
  }
}
```

## 주요 기능

### 1. 사용자 설정 기반 필터링

디스패처는 자동으로 사용자의 알림 설정을 확인하고 필터링합니다:

```python
# NotificationPreference에서 설정 확인
# enable_proposal_notifications = False인 경우
# 의뢰 관련 알림은 전송되지 않음
dispatcher.notify_proposal_matched(...)  # 전송 안 됨
```

### 2. 다중 디바이스 지원

한 사용자가 여러 디바이스를 등록한 경우 모든 활성 디바이스로 알림 전송:

```python
# 사용자의 모든 활성 디바이스로 전송
fcm_service.send_to_user(
    db=db,
    user_id=123,
    notification_type=NotificationType.OFFER_NEW,
    title="새 제안",
    body="새로운 제안이 도착했습니다."
)
```

### 3. 전송 상태 추적

알림 전송 상태를 데이터베이스에 기록:

- `PENDING`: 전송 대기 중
- `SENT`: FCM으로 전송됨
- `DELIVERED`: 디바이스에 전달됨
- `FAILED`: 전송 실패
- `READ`: 사용자가 읽음

### 4. 에러 핸들링

```python
# FCM 전송 결과 확인
notification, results = fcm_service.send_to_user(...)

for result in results:
    if result.success:
        print(f"Success: {result.message_id}")
    else:
        print(f"Failed: {result.error_code} - {result.error_message}")
        # 에러 코드:
        # - UNREGISTERED: 토큰이 더 이상 유효하지 않음
        # - INVALID_ARGUMENT: 잘못된 인자
        # - SENDER_ID_MISMATCH: 발신자 ID 불일치
```

### 5. 토픽 기반 브로드캐스트

특정 주제를 구독한 모든 사용자에게 전송:

```python
fcm_service.send_to_topic(
    topic="all_runners",
    title="새로운 의뢰가 등록되었습니다!",
    body="강남역 근처에서 배달 요청이 있습니다.",
    data={"proposal_id": "789"}
)
```

## 디버깅 및 로깅

로깅 설정:

```python
import logging

# 알림 관련 로그 확인
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 로그 출력 예시:
# INFO - Successfully sent message to token abc123... Message ID: xyz789
# WARNING - No active device tokens found for user 123
# ERROR - Failed to initialize Firebase Admin SDK: ...
```

## 보안 고려사항

1. **서비스 계정 키 보호**
   - `.gitignore`에 `keys/` 디렉토리 추가
   - 프로덕션에서는 환경 변수 또는 시크릿 관리 서비스 사용

2. **디바이스 토큰 검증**
   - 사용자는 자신의 토큰만 등록/수정/삭제 가능
   - JWT 인증을 통한 API 접근 제어

3. **알림 권한 확인**
   - 사용자 설정 기반 필터링
   - 개인정보 보호를 위한 데이터 암호화 고려

## 테스트

### 단위 테스트 예시

```python
import pytest
from app.services.fcm_service import FCMService
from app.services.notification_dispatcher import NotificationDispatcher

def test_send_notification(db_session):
    fcm_service = FCMService(credentials_path="./test-credentials.json")
    dispatcher = NotificationDispatcher(fcm_service)

    # 알림 전송 테스트
    dispatcher.notify_proposal_matched(
        db=db_session,
        proposal_id=1,
        customer_id=1,
        runner_id=2,
        proposal_title="Test Proposal"
    )

    # 알림이 생성되었는지 확인
    notifications = db_session.query(Notification).filter(
        Notification.user_id == 1
    ).all()

    assert len(notifications) > 0
    assert notifications[0].notification_type == NotificationType.PROPOSAL_MATCHED
```

## 문제 해결

### Firebase Admin SDK 초기화 실패

**문제:** `Failed to initialize Firebase Admin SDK`

**해결:**
1. 서비스 계정 키 파일 경로 확인
2. 파일이 유효한 JSON인지 확인
3. Firebase 프로젝트가 활성화되어 있는지 확인

### 토큰 전송 실패 (UNREGISTERED)

**문제:** `Device token is no longer valid`

**해결:**
1. 클라이언트에서 새 토큰 받기
2. 서버에 토큰 재등록
3. 만료된 토큰 비활성화 또는 삭제

### 알림이 전송되지 않음

**확인사항:**
1. 사용자가 활성 디바이스 토큰을 등록했는지 확인
2. 사용자의 알림 설정 확인 (`NotificationPreference`)
3. FCM 서비스가 제대로 초기화되었는지 확인
4. 로그에서 에러 메시지 확인

## 다음 단계

1. **알림 템플릿 시스템**: 다국어 지원 및 템플릿 기반 알림
2. **스케줄링**: 특정 시간에 알림 전송
3. **배치 처리**: 대량 알림 전송 최적화
4. **분석**: 알림 오픈율, 클릭률 추적
5. **A/B 테스트**: 알림 메시지 효과 테스트

## 참고 자료

- [Firebase Cloud Messaging 문서](https://firebase.google.com/docs/cloud-messaging)
- [Firebase Admin SDK for Python](https://firebase.google.com/docs/admin/setup)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
