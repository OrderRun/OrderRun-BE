# 알림 정책 (Notification Policy)

> 마지막 업데이트: 2026-06-02

## 도메인 용어 매핑

| 내부 코드 용어 | 사용자 표시 용어 |
|---|---|
| Proposal (요청) | 게시물 |
| Offer (제안) | 지원 |
| Orderer (오더러) | 요청자 |
| Runner (러너) | 지원자 |
| 행님 | 요청자 |
| 꼬봉 | 지원자 |
| complete_delivery | 지원자 만남 확인 ("만났어요") |
| confirm_received | 요청자 만남 확인 ("만났어요") |

---

## 저장 및 발송 조건

클라이언트 전달용 FCM payload 계약은 [`../api-spec/notification-fcm-payload.md`](../api-spec/notification-fcm-payload.md)를 기준으로 한다.

모든 도메인 이벤트 알림은 알림 히스토리용 `notifications` 레코드로 저장한다.
수신자의 `alarm_enabled` 값은 레코드 생성 여부가 아니라 푸시 발송 여부를 결정한다.

- `alarm_enabled = true` → `status=PENDING` 저장 후 FCM 발송 대상
- `alarm_enabled = false` → `status=SKIPPED` 저장 후 FCM 미발송

`SKIPPED` 알림은 사용자가 나중에 알림 설정을 켜도 소급 발송하지 않는다. 읽기 전까지 `read_at=null`로 유지되며 알림 목록과 미읽음 카운트에 포함된다.

---

## 발송 아키텍처: Outbox 패턴 + Event Publisher/Listener

```
[비즈니스 트랜잭션]
  비즈니스 서비스 (OfferService, ProposalService)
      → EventBus.publish(DomainEvent, db)  ← 같은 DB 세션
      → NotificationEventListener
          → Notification INSERT (alarm_enabled=true: PENDING, false: SKIPPED)
    → db.commit()  ← 비즈니스 데이터 + PENDING 알림 함께 커밋

[비동기 발송 - FastAPI BackgroundTask]
  API 응답 후 즉시 실행
  → NotificationWorker.flush_pending(SessionLocal)
    → PENDING 알림 조회 → FCM 발송 → SENT / FAILED 업데이트

[배치 재시도 - APScheduler, 5분 주기]
  → NotificationWorker.retry_failed(SessionLocal)
    → FAILED 중 retry_count < 3 조회 → FCM 재발송
    → 성공: SENT / 실패: retry_count + 1
```

---

## 1차 구현 알림 목록

### 지원 관련

| 이벤트 | 수신자 | NotificationType | 타이틀 | 내용 | 트리거 |
|---|---|---|---|---|---|
| 지원자 발생 | 요청자 | `OFFER_NEW` | 누군가 지원했어요! 👀 | 회원님의 요청에 새로운 지원자가 생겼어요. 확인해보세요! | `POST /v1/offer` |
| 지원 완료 | 지원자 | `OFFER_SUBMITTED` | 지원 완료! ✅ | 지원이 정상적으로 접수됐어요. 요청자의 선택을 기다려주세요. | `POST /v1/offer` |
| 지원 수락 | 지원자 | `OFFER_ACCEPTED` | 선택받으셨어요! 🙌 | 요청자가 회원님을 선택했어요. | `POST /v1/offer/{id}/accept` |
| 탈락 통보 | 탈락 지원자 전원 | `OFFER_REJECTED` | 이번엔 아쉽게 됐어요 😢 | 이번엔 선택받지 못했지만 다음 기회가 분명 있을 거예요. | `POST /v1/offer/{id}/accept` |

### 만남 확인 관련

| 이벤트 | 수신자 | NotificationType | 타이틀 | 내용 | 트리거 |
|---|---|---|---|---|---|
| 지원자만 만남 확인 | 요청자 | `MEETING_CONFIRMED` | 지원자가 만남을 확인했어요! 🤝 | 지원자가 만남을 확인했어요. 회원님도 확인해주시면 정산이 바로 진행돼요. | `POST /v1/offer/{id}/complete-delivery` |
| 요청자만 만남 확인 | 지원자 | `MEETING_CONFIRMED` | 요청자가 만남을 확인했어요! 🤝 | 요청자가 만남을 확인했어요. 회원님도 확인해주시면 정산이 진행돼요! | `POST /v1/proposal/{id}/confirm-received` |
| 양측 확인 완료 | 요청자 + 지원자 | `EXECUTION_COMPLETED` | 완료! 수고하셨어요 🎊 | 양측 만남이 모두 확인됐어요. 성공적으로 완료됐습니다! | `POST /v1/offer/{id}/complete-delivery` 또는 `POST /v1/proposal/{id}/confirm-received` |

양측 확인 완료 알림은 두 번째 완료 클릭으로 `ALL_COMPLETED`가 되는 경우에만 발송한다. 이때 마지막 클릭에 대한 `MEETING_CONFIRMED`는 별도로 발송하지 않고 `EXECUTION_COMPLETED`만 발송한다.

### 분쟁 관련

| 이벤트 | 수신자 | NotificationType | 타이틀 | 내용 | 트리거 |
|---|---|---|---|---|---|
| 요청자가 분쟁 접수 | 지원자 | `DISPUTE_RAISED` | 분쟁이 접수되었어요 | 요청자가 분쟁을 접수했어요. 앱에서 내용을 확인해주세요. | `POST /v1/proposal/{id}/dispute` |
| 지원자가 분쟁 접수 | 요청자 | `DISPUTE_RAISED` | 분쟁이 접수되었어요 | 지원자가 분쟁을 접수했어요. 앱에서 내용을 확인해주세요. | `POST /v1/offer/{id}/dispute` |

### 저장 필드와 FCM data

현재 1차 알림은 모두 `related_entity_type="offer"`, `related_entity_id=<offer_id>`로 저장한다. 이 값은 서버 알림 조회/관리용 DB 필드이며 FCM data payload에는 포함하지 않는다.

`notifications.data`에는 JSON 문자열로 `offer_id`, `proposal_id`를 저장한다. `NotificationWorker`가 FCM으로 전달하는 data payload는 다음 JSON 형태다.

```json
{
  "notification_type": "offer_accepted",
  "offer_id": "45",
  "proposal_id": "10"
}
```

| 필드 | 의미 |
|---|---|
| `notification_type` | `NotificationType` 값. 클라이언트의 현재 라우팅 code로 사용할 수 있다. |
| `offer_id` | `notifications.data.offer_id` |
| `proposal_id` | `notifications.data.proposal_id` |

명시적인 `navigation_code`, `target_page`, `deep_link` 필드는 아직 없다. 클라이언트 딥링크 정책을 추가할 때는 위 payload와 별도 호환 정책을 정해야 한다.

### 현재 구현 주의사항

- `POST /v1/proposal/{id}/confirm-received`는 알림 레코드를 생성하지만 현재 라우터에서 `NotificationWorker.flush_pending(SessionLocal)` background task를 등록하지 않는다. 즉시 FCM 발송이 필요하면 라우터에 background task 연결을 추가해야 한다.
- 이벤트 기반 outbox 발송은 클라이언트 payload를 `notification_type`, `offer_id`, `proposal_id`로 제한한다. 커스텀 알림 직접 발송 경로는 별도 경로로 기존 data prefix를 사용할 수 있다.

---

## 2차 구현 대상 (현재 불가)

| 이벤트 | 미구현 이유 | 선행 조건 |
|---|---|---|
| 채팅방 개설 + 입장 코드 발급 | 카카오톡 연동 없음 | 채팅방 API 구현 |
| 만남 확인 리마인드 1차 (2시간 후) | 시간 기반 트리거 | APScheduler 시간 조건 추가 |
| 만남 확인 리마인드 2차 (6시간 후) | 시간 기반 트리거 | 동일 |
| 웨이팅비 정산 완료 | 정산 실행 API 없음 | 정산 처리 API 구현 |
| 입금 미확인 시간 초과 (30분) | 시간 기반 트리거 | 스케줄러 조건 추가 |
| 게시물 만료 (48시간 미선택) | 시간 기반 트리거 | 스케줄러 조건 추가 |

---

## NotificationType 매핑

| 정책 이벤트 | NotificationType |
|---|---|
| 지원자 발생 (요청자) | `OFFER_NEW` |
| 지원 완료 (지원자) | `OFFER_SUBMITTED` |
| 지원 수락 | `OFFER_ACCEPTED` |
| 탈락 통보 | `OFFER_REJECTED` |
| 지원자/요청자 만남 확인 | `MEETING_CONFIRMED` |
| 양측 완료 | `EXECUTION_COMPLETED` |
| 분쟁 접수 | `DISPUTE_RAISED` |

---

## 발송 제한 (1차)

- 재시도 최대 3회 (`retry_count < 3`)
- `SKIPPED` 상태는 발송 및 재시도 대상에서 제외
- 지원 알림 묶음 처리 (5회/시간): **2차 구현**
