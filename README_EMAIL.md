# 이메일 발송 모듈 사용 가이드

OrderRun 백엔드의 이메일 발송 모듈 사용법을 안내합니다.

## 목차
- [설정](#설정)
- [기본 사용법](#기본-사용법)
- [템플릿 이메일](#템플릿-이메일)
- [대량 발송](#대량-발송)
- [데이터베이스 로깅](#데이터베이스-로깅)

## 설정

### 1. 의존성 설치

```bash
pip install -e .
```

필요한 패키지:
- `aiosmtplib>=3.0.0` - 비동기 SMTP 클라이언트
- `jinja2>=3.1.0` - HTML 템플릿 엔진
- `email-validator>=2.0.0` - 이메일 주소 검증

### 2. 환경 변수 설정

`.env` 파일에 다음 설정을 추가하세요:

```bash
# Email (SMTP) - Gmail 사용 예시
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
EMAIL_FROM=your-email@gmail.com
EMAIL_FROM_NAME=OrderRun
```

#### Gmail 앱 비밀번호 생성 방법:
1. Google 계정 설정 → 보안
2. 2단계 인증 활성화
3. 앱 비밀번호 생성
4. 생성된 16자리 비밀번호를 `SMTP_PASSWORD`에 설정

### 3. 데이터베이스 마이그레이션

이메일 로그 테이블을 생성하기 위해 마이그레이션을 실행하세요:

```bash
alembic revision --autogenerate -m "Add email log table"
alembic upgrade head
```

## 기본 사용법

### 단일 이메일 발송

```python
from sqlalchemy.orm import Session
from app.services.email_service import email_service
from app.schemas.email import EmailRecipient, EmailSendRequest

async def send_simple_email(db: Session):
    """간단한 이메일 발송 예시"""

    request = EmailSendRequest(
        to=EmailRecipient(
            email="user@example.com",
            name="홍길동"
        ),
        subject="테스트 이메일",
        body_text="안녕하세요, 이것은 텍스트 이메일입니다.",
        body_html="<h1>안녕하세요</h1><p>이것은 HTML 이메일입니다.</p>"
    )

    result = await email_service.send_email(db, request)

    if result.success:
        print(f"이메일 발송 성공: {result.email_log_id}")
    else:
        print(f"이메일 발송 실패: {result.error_message}")
```

### HTML만 사용하는 경우

```python
request = EmailSendRequest(
    to=EmailRecipient(email="user@example.com"),
    subject="HTML 이메일",
    body_html="<div style='color: blue;'><h2>HTML 이메일</h2></div>"
)
```

### 발신자 정보 커스터마이징

```python
request = EmailSendRequest(
    to=EmailRecipient(email="user@example.com"),
    subject="커스텀 발신자",
    body_html="<p>커스텀 발신자 정보</p>",
    from_email="custom@orderrun.com",
    from_name="OrderRun 고객센터"
)
```

## 템플릿 이메일

### 사용 가능한 템플릿

#### 1. 환영 이메일 (`welcome.html`)

```python
from datetime import datetime
from app.schemas.email import EmailTemplateRequest

async def send_welcome_email(db: Session, user_email: str, user_name: str):
    """신규 회원 환영 이메일"""

    request = EmailTemplateRequest(
        to=EmailRecipient(email=user_email, name=user_name),
        template_name="welcome",
        subject="OrderRun에 오신 것을 환영합니다!",
        context={
            "user_name": user_name,
            "verification_link": "https://orderrun.com/verify?token=abc123",
            "current_year": datetime.now().year
        },
        user_id=1  # Optional: 사용자 ID
    )

    result = await email_service.send_template_email(db, request)
    return result
```

#### 2. 알림 이메일 (`notification.html`)

```python
async def send_proposal_notification(
    db: Session,
    user_email: str,
    proposal_id: int,
    runner_name: str
):
    """제안 받음 알림 이메일"""

    request = EmailTemplateRequest(
        to=EmailRecipient(email=user_email),
        template_name="notification",
        subject="새로운 제안이 도착했습니다",
        context={
            "user_name": "홍길동",
            "notification_title": "새로운 제안",
            "notification_message": "귀하의 요청에 대한 새로운 제안이 도착했습니다.",
            "notification_details": {
                "제안 ID": str(proposal_id),
                "러너": runner_name,
                "금액": "15,000원"
            },
            "action_url": f"https://orderrun.com/proposals/{proposal_id}",
            "action_text": "제안 확인하기",
            "additional_message": "24시간 내에 응답해주세요."
        }
    )

    result = await email_service.send_template_email(db, request)
    return result
```

#### 3. 비밀번호 재설정 (`password_reset.html`)

```python
async def send_password_reset_email(
    db: Session,
    user_email: str,
    reset_token: str
):
    """비밀번호 재설정 이메일"""

    request = EmailTemplateRequest(
        to=EmailRecipient(email=user_email),
        template_name="password_reset",
        subject="비밀번호 재설정 요청",
        context={
            "user_name": "홍길동",
            "reset_link": f"https://orderrun.com/reset-password?token={reset_token}",
            "expiry_hours": "24"
        }
    )

    result = await email_service.send_template_email(db, request)
    return result
```

### 커스텀 템플릿 생성

`app/templates/email/` 디렉토리에 새로운 HTML 파일을 생성하세요:

```html
<!-- app/templates/email/custom.html -->
{% extends "base.html" %}

{% block title %}커스텀 이메일 - OrderRun{% endblock %}

{% block header_title %}커스텀 헤더{% endblock %}

{% block content %}
<h2>안녕하세요 {{ user_name }}님!</h2>

<p>{{ custom_message }}</p>

{% if show_button %}
<p style="text-align: center;">
    <a href="{{ button_url }}" class="button">{{ button_text }}</a>
</p>
{% endif %}
{% endblock %}
```

사용 예시:

```python
request = EmailTemplateRequest(
    to=EmailRecipient(email="user@example.com"),
    template_name="custom",
    subject="커스텀 이메일",
    context={
        "user_name": "홍길동",
        "custom_message": "이것은 커스텀 메시지입니다.",
        "show_button": True,
        "button_url": "https://orderrun.com",
        "button_text": "지금 확인하기"
    }
)
```

## 대량 발송

여러 사용자에게 동일한 내용의 이메일을 발송할 때 사용합니다:

```python
from app.schemas.email import EmailBulkSendRequest

async def send_announcement_email(db: Session):
    """공지사항 대량 발송"""

    request = EmailBulkSendRequest(
        recipients=[
            EmailRecipient(email="user1@example.com", name="사용자1"),
            EmailRecipient(email="user2@example.com", name="사용자2"),
            EmailRecipient(email="user3@example.com", name="사용자3"),
        ],
        subject="[공지] 서비스 업데이트 안내",
        body_html="""
            <h2>안녕하세요!</h2>
            <p>OrderRun 서비스가 업데이트되었습니다.</p>
            <ul>
                <li>새로운 기능 추가</li>
                <li>성능 개선</li>
                <li>버그 수정</li>
            </ul>
        """
    )

    result = await email_service.send_bulk_email(db, request)

    print(f"총 {result.total}개 발송 시도")
    print(f"성공: {result.successful}개")
    print(f"실패: {result.failed}개")

    # 개별 결과 확인
    for res in result.results:
        if not res.success:
            print(f"실패: {res.to_email} - {res.error_message}")
```

## 데이터베이스 로깅

모든 이메일 발송 내역은 자동으로 `email_logs` 테이블에 저장됩니다.

### 이메일 로그 조회

```python
from app.models.email import EmailStatus

# 특정 사용자의 이메일 로그 조회
logs = email_service.get_email_logs(
    db=db,
    user_id=1,
    limit=10
)

# 실패한 이메일만 조회
failed_logs = email_service.get_email_logs(
    db=db,
    status=EmailStatus.FAILED,
    limit=50
)

# 로그 출력
for log in logs:
    print(f"[{log.status}] {log.to_email} - {log.subject}")
    if log.error_message:
        print(f"  오류: {log.error_message}")
```

### 이메일 상태

- `PENDING`: 발송 대기 중
- `SENT`: 발송 완료
- `FAILED`: 발송 실패
- `BOUNCED`: 반송됨
- `DELIVERED`: 전달 확인됨

## API 엔드포인트에서 사용 예시

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.email_service import email_service
from app.schemas.email import EmailSendRequest, EmailSendResult

router = APIRouter()

@router.post("/send-email", response_model=EmailSendResult)
async def send_email_endpoint(
    request: EmailSendRequest,
    db: Session = Depends(get_db)
):
    """이메일 발송 API 엔드포인트"""
    result = await email_service.send_email(db, request)
    return result
```

## 백그라운드 작업에서 사용

FastAPI의 BackgroundTasks를 활용한 비동기 발송:

```python
from fastapi import BackgroundTasks

async def send_email_background(
    background_tasks: BackgroundTasks,
    db: Session,
    user_email: str
):
    """백그라운드에서 이메일 발송"""

    async def send_task():
        request = EmailTemplateRequest(
            to=EmailRecipient(email=user_email),
            template_name="welcome",
            subject="환영합니다",
            context={"user_name": "사용자"}
        )
        await email_service.send_template_email(db, request)

    background_tasks.add_task(send_task)
```

## 이벤트 디스패처 통합

기존 notification_dispatcher와 통합하여 사용:

```python
from app.services.notification_dispatcher import notification_dispatcher

# 푸시 알림과 이메일을 함께 발송
await notification_dispatcher.dispatch_notification(
    db=db,
    user_id=user_id,
    notification_type=NotificationType.PROPOSAL_NEW,
    title="새로운 제안",
    body="제안이 도착했습니다."
)

# 추가로 이메일 발송
await email_service.send_template_email(db, email_request)
```

## 문제 해결

### Gmail "Less secure app" 오류
- Gmail 앱 비밀번호를 사용하세요 (2단계 인증 필요)

### 템플릿을 찾을 수 없음
- 템플릿 파일이 `app/templates/email/` 디렉토리에 있는지 확인
- 파일 확장자가 `.html`인지 확인

### SMTP 연결 실패
- 방화벽에서 SMTP 포트(587 또는 465)가 열려있는지 확인
- SMTP 서버 주소와 포트 번호가 올바른지 확인

## 참고 자료

- [aiosmtplib 문서](https://aiosmtplib.readthedocs.io/)
- [Jinja2 템플릿 문서](https://jinja.palletsprojects.com/)
- [Gmail SMTP 설정](https://support.google.com/mail/answer/7126229)
