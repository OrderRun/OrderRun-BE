# Starlette 핵심 아키텍처: 이벤트 루프, 스레드 풀, BackgroundTasks

> FastAPI의 기반인 Starlette가 비동기 요청, 동기 요청, 응답 후 작업을 처리하는 방식

FastAPI는 HTTP 계층에서 Starlette를 사용한다. 따라서 FastAPI의 `async def`, 일반 `def`, `BackgroundTasks`의 실행 모델을 이해하려면 Starlette와 AnyIO의 역할을 함께 봐야 한다.

## 1. 먼저 잡을 모델: 프로세스 안의 이벤트 루프

**Uvicorn worker 1개는 FastAPI 앱을 실행하는 프로세스 1개**다. 그 프로세스 안에는 메인 스레드, 이벤트 루프, 동기 작업을 위한 AnyIO 스레드 풀이 있다.

```text
Uvicorn application worker 프로세스 1개
├─ 메인 스레드 1개
│  └─ 이벤트 루프 1개
│     └─ async def 요청·비동기 I/O 처리
│
└─ AnyIO 스레드 풀
   ├─ 일반 def 엔드포인트 실행
   ├─ 동기 의존성 실행
   └─ 동기 BackgroundTasks 실행
```

worker를 2개 띄우면 위 구조가 두 세트 생긴다. 각 worker는 이벤트 루프, 스레드 풀, 메모리, DB 커넥션 풀을 서로 공유하지 않는다.

```text
Uvicorn worker 프로세스 1  → 이벤트 루프 1 + 스레드 풀 1
Uvicorn worker 프로세스 2  → 이벤트 루프 2 + 스레드 풀 2
```

이벤트 루프는 I/O를 기다리는 코루틴과 실행 가능한 코루틴을 관리한다. `await`를 만난 코루틴은 I/O 등의 완료를 기다리는 동안 제어권을 이벤트 루프에 돌려준다. 그 사이 이벤트 루프는 다른 준비된 요청을 실행할 수 있다.

```text
클라이언트 요청
    │
    ▼
Uvicorn worker 프로세스
└─ 메인 스레드의 이벤트 루프
   ├─ async def 엔드포인트 → 이벤트 루프에서 실행
   │  └─ await에서 제어권을 돌려주면 다른 코루틴을 처리
   │
   └─ def 엔드포인트 → AnyIO 스레드 풀로 위임
```

`async def`가 항상 빠르다는 뜻은 아니다. `async def` 안에서 CPU를 오래 점유하거나 동기 I/O를 직접 실행하면 이벤트 루프가 막혀 같은 worker의 다른 요청 처리도 지연된다.

## 2. `async def`와 일반 `def`의 차이

### `async def` 엔드포인트

`async def`로 선언한 엔드포인트는 이벤트 루프에서 직접 실행된다. 네트워크·DB·파일 I/O처럼 대기 시간이 있는 작업은 해당 라이브러리의 비동기 API를 사용하고 `await`해야 동시성의 이점을 얻는다.

```python
@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    order = await repository.get(order_id)
    return order
```

### 일반 `def` 엔드포인트

Starlette는 일반 `def` 엔드포인트가 이벤트 루프를 막지 않도록 AnyIO의 `anyio.to_thread.run_sync`를 통해 스레드 풀에서 실행한다. 동기 의존성이나 동기 background task에도 같은 제한이 공유될 수 있다.

```python
@app.get("/reports/{report_id}")
def get_report(report_id: int):
    return report_service.load(report_id)  # 동기 코드
```

스레드 풀의 기본 동시 실행 한도는 **40 토큰**이다. 이는 `ThreadPoolExecutor`의 CPU 코어 기반 기본값이 아니라 AnyIO의 capacity limiter 설정이다. 40개의 동기 작업이 이미 실행 중이면 다음 동기 작업은 토큰이 반환될 때까지 `await` 상태로 대기한다. 이때 이벤트 루프 전체가 멈추는 것이 아니라, 해당 작업만 진행하지 못하고 다른 실행 가능한 코루틴은 계속 처리된다.

> 토큰 수를 무작정 늘리면 메모리와 스케줄링 비용이 증가한다. 동기 I/O가 많아 병목이 확인된 경우에만 부하 측정 후 조정한다.

## 3. `BackgroundTasks`는 전역 작업 큐가 아니다

Starlette의 `BackgroundTask`와 `BackgroundTasks`는 **프로세스 내부의 응답 후 작업** 기능이다. `BackgroundTasks` 객체는 요청 처리 중 만들어져 그 응답에 연결된다. HTTP 응답 전송이 끝난 뒤, 그 응답에 등록된 작업을 실행한다.

```text
요청 처리 중 BackgroundTasks.add_task(...)
    │
    ▼
응답 객체에 작업 목록 연결
    │
    ▼
HTTP 응답 전송 완료
    │
    ▼
해당 응답의 작업을 등록 순서대로 실행
    ├─ async def 작업 → 이벤트 루프에서 await
    └─ def 작업       → AnyIO 스레드 풀에서 실행
```

따라서 이를 모든 요청이 공유하는 “무제한 메모리 큐”로 보기는 정확하지 않다. 등록된 작업 목록 자체는 메모리에 있지만, 별도 브로커·영속 저장소·재시도 기능이 있는 작업 큐는 아니다.

여러 작업을 등록하면 순서대로 실행된다. 앞선 작업에서 예외가 발생하면 뒤의 작업은 실행되지 않는다.

### 요청 기반 알림에는 적합하다

SMS 인증번호, 이메일, 푸시 알림처럼 **사용자의 API 요청이 발송을 시작하는 작업**에 적합하다. 클라이언트는 발송 완료를 기다리지 않고 응답을 받고, 서버는 응답 전송 뒤 발송을 시도한다.

```text
사용자의 인증번호 요청
    │
    ▼
인증 정보 DB 저장 + SMS 발송 작업 등록
    │
    ▼
HTTP 응답 반환
    │
    ▼
BackgroundTasks가 SMS 발송 시도
```

발송이 실패해도 HTTP 응답은 이미 전송된 상태다. 서비스 정책이 허용한다면 사용자는 인증번호 재발송 API를 다시 요청할 수 있다. 다만 `BackgroundTasks`만으로는 실패한 발송을 자동 재시도하거나 발송 완료를 보장하지 않는다.

### 요청 없는 자동 알림에는 맞지 않는다

“매일 오전 9시에 미수행 사용자에게 푸시 발송”처럼 정해진 시간이나 조건으로 시작하는 자동 알림에는 HTTP 요청이 없다. `BackgroundTasks`는 HTTP **응답에 연결**해야 하므로, 이런 작업을 스스로 시작할 수 없다.

```text
스케줄러가 정해진 시간에 실행
    │
    ▼
발송 대상 조회
    │
    ├─ 작은 서비스: APScheduler가 직접 발송
    │
    └─ 발송 보장·재시도 필요: 작업 큐에 등록
                                  │
                                  ▼
                           Celery worker가 발송
```

즉, 자동 알림을 **보내는 것 자체가 불가능한 것은 아니지만**, `BackgroundTasks`의 용도는 아니다. 스케줄러가 실행 시점을 만들고, 신뢰성 요구가 커지면 Celery 같은 영속 작업 큐가 실제 발송을 처리한다.

```python
from fastapi import BackgroundTasks


def send_email(address: str) -> None:
    ...


async def refresh_cache() -> None:
    ...


@app.post("/signup")
async def signup(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, "user@example.com")
    background_tasks.add_task(refresh_cache)
    return {"ok": True}
```

## 4. 언제 사용하고, 언제 별도 큐를 써야 하나

`BackgroundTasks`는 응답을 먼저 반환해도 되는 작은 작업에 적합하다. 예를 들면 이메일·SMS 발송, 짧은 알림 처리, 로그 기록이 있다.

다음 요구가 있으면 Celery, Dramatiq, RQ 같은 별도 작업 시스템과 메시지 브로커를 검토해야 한다.

- 프로세스 재시작 뒤에도 작업을 보존해야 한다.
- 실패 재시도, 지연 실행, 작업 상태 추적이 필요하다.
- CPU 사용량이 크거나 오래 걸리는 작업을 처리해야 한다.
- 여러 서버에 작업을 분산해야 한다.

## 5. OrderRun에서의 사용 사례

현재 프로젝트는 FastAPI의 `BackgroundTasks`를 동기 함수와 함께 사용한다.

### SMS 인증번호 발송

[`app/api/v1/auth.py`](../../../app/api/v1/auth.py)의 `signup_send()`는 `BackgroundTasks`를 주입받아 서비스에 전달한다. [`app/services/user_auth_service.py`](../../../app/services/user_auth_service.py)는 DB 커밋 후 아래처럼 SMS 발송을 등록한다.

```python
background_tasks.add_task(self._send_sms_safely, phone, message)
```

회원가입과 로그인 인증번호 발송 메서드는 `BackgroundTasks`를 필수로 받는다. 따라서 `None` 여부에 따라 동기 발송으로 전환하지 않고, DB 저장이 완료된 뒤 항상 응답 후 작업으로 등록한다.

`_send_sms_safely`는 일반 `def`이므로 응답 전송 뒤 AnyIO 스레드 풀에서 실행된다. 즉, 인증번호 발송 실패가 이미 완료된 HTTP 응답을 바꾸지는 않는다. 이 특성은 현재 통합 테스트의 `test_signup_send_persists_verification_even_if_background_sms_fails`가 검증한다.

### 알림 발송 대기 항목 처리

[`app/api/v1/offer.py`](../../../app/api/v1/offer.py)의 `create_offer()` 등은 제안 처리 후 다음 작업을 등록한다.

```python
background_tasks.add_task(get_notification_worker().flush_pending, SessionLocal)
```

`flush_pending`도 일반 `def`이므로 스레드 풀 토큰을 사용한다. 외부 FCM 호출이나 DB 작업이 오래 걸리면 다른 동기 엔드포인트·의존성과 40 토큰 한도를 공유하므로, 처리 시간과 실패율을 관찰해야 한다.

## 6. 핵심 정리

| 구성 요소 | 역할 | 주의점 |
|---|---|---|
| 이벤트 루프 | `async def` 코루틴과 I/O 대기를 조율 | 동기 I/O·무거운 CPU 작업을 직접 실행하면 막힌다. |
| AnyIO 스레드 풀 | 일반 `def` 엔드포인트와 동기 background task 실행 | 기본 동시 실행 한도는 40 토큰이며 공유된다. |
| `BackgroundTasks` | 응답 전송 후 실행할 작업을 응답에 연결 | 영속 큐가 아니며, 작업은 순차 실행되고 예외가 나면 이후 작업이 중단된다. |

## 참고 자료

- [Starlette Thread Pool](https://www.starlette.io/threadpool/)
- [Starlette Background Tasks](https://www.starlette.io/background/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
