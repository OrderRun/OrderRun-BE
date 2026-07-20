# Notification FCM Payload

이 문서는 클라이언트가 푸시 알림 수신/클릭 처리에 사용할 FCM payload 계약을 정리한다.

## 공통 규칙

- 모든 자동 알림은 수신자의 `alarm_enabled=true`일 때만 생성된다.
- FCM `notification.title`, `notification.body`에는 아래 표의 타이틀/내용이 들어간다.
- FCM `data`의 모든 값은 문자열이다.
- 발송자 사용자 ID는 현재 payload에 포함하지 않는다. 아래 표의 발송자는 알림을 발생시킨 역할/행위자를 뜻한다.
- 클라이언트 라우팅 code로는 `data.notification_type` 값을 사용한다.
- 자동 알림 payload는 `notification_type`, `offer_id`, `proposal_id`만 전달한다.

## 공통 data 형태

```json
{
  "notification_type": "offer_accepted",
  "offer_id": "45",
  "proposal_id": "10"
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `notification_type` | string | 클라이언트 라우팅 code |
| `offer_id` | string | Offer ID |
| `proposal_id` | string | Proposal ID |

## 이벤트별 알림 계약

| 이벤트 | 수신자 | 발송자/원인 | 트리거 | title | body |
|---|---|---|---|---|---|
| 지원자 발생 | 요청자 | 지원자 | `POST /v1/offer` | `누군가 지원했어요! 👀` | `회원님의 요청에 새로운 지원자가 생겼어요. 확인해보세요!` |
| 지원 완료 | 지원자 | 지원자 본인 | `POST /v1/offer` | `지원 완료! ✅` | `지원이 정상적으로 접수됐어요. 요청자의 선택을 기다려주세요.` |
| 지원 수락 | 선택된 지원자 | 요청자 | `POST /v1/offer/{offerId}/accept` | `선택받으셨어요! 🙌` | `요청자가 회원님을 선택했어요.` |
| 탈락 통보 | 탈락 지원자 전원 | 요청자 | `POST /v1/offer/{offerId}/accept` | `이번엔 아쉽게 됐어요 😢` | `이번엔 선택받지 못했지만 다음 기회가 분명 있을 거예요.` |
| 지원자만 만남 확인 | 요청자 | 지원자 | `POST /v1/offer/{offerId}/complete-delivery` | `지원자가 만남을 확인했어요! 🤝` | `지원자가 만남을 확인했어요. 회원님도 확인해주시면 정산이 바로 진행돼요.` |
| 요청자만 만남 확인 | 지원자 | 요청자 | `POST /v1/proposal/{proposalId}/confirm-received` | `요청자가 만남을 확인했어요! 🤝` | `요청자가 만남을 확인했어요. 회원님도 앱에서 만남을 확인해주시면 정산이 진행돼요!` |
| 양측 확인 완료 | 요청자 + 지원자 | 두 번째 완료 클릭 사용자 | `POST /v1/offer/{offerId}/complete-delivery` 또는 `POST /v1/proposal/{proposalId}/confirm-received` | `완료! 수고하셨어요 🎊` | `양측 만남이 모두 확인됐어요. 성공적으로 완료됐습니다!` |

양측 확인 완료는 두 번째 완료 클릭으로 `ALL_COMPLETED`가 되는 경우에만 발송된다. 이때 마지막 클릭에 대한 `meeting_confirmed`는 별도로 발송되지 않는다.
| 요청자가 분쟁 접수 | 지원자 | 요청자 | `POST /v1/proposal/{proposalId}/dispute` | `분쟁이 접수되었어요` | `요청자가 분쟁을 접수했어요. 앱에서 내용을 확인해주세요.` |
| 지원자가 분쟁 접수 | 요청자 | 지원자 | `POST /v1/offer/{offerId}/dispute` | `분쟁이 접수되었어요` | `지원자가 분쟁을 접수했어요. 앱에서 내용을 확인해주세요.` |

## 이벤트별 data payload

### 지원자 발생

```json
{
  "notification_type": "offer_new",
  "offer_id": "{offerId}",
  "proposal_id": "{proposalId}"
}
```

### 지원 완료

```json
{
  "notification_type": "offer_submitted",
  "offer_id": "{offerId}",
  "proposal_id": "{proposalId}"
}
```

### 지원 수락

```json
{
  "notification_type": "offer_accepted",
  "offer_id": "{acceptedOfferId}",
  "proposal_id": "{proposalId}"
}
```

### 탈락 통보

```json
{
  "notification_type": "offer_rejected",
  "offer_id": "{acceptedOfferId}",
  "proposal_id": "{proposalId}"
}
```

### 지원자만 만남 확인

```json
{
  "notification_type": "meeting_confirmed",
  "offer_id": "{offerId}",
  "proposal_id": "{proposalId}"
}
```

### 요청자만 만남 확인

```json
{
  "notification_type": "meeting_confirmed",
  "offer_id": "{offerId}",
  "proposal_id": "{proposalId}"
}
```

### 양측 확인 완료

```json
{
  "notification_type": "execution_completed",
  "offer_id": "{offerId}",
  "proposal_id": "{proposalId}"
}
```

### 요청자가 분쟁 접수

```json
{
  "notification_type": "dispute_raised",
  "offer_id": "{offerId}",
  "proposal_id": "{proposalId}"
}
```

### 지원자가 분쟁 접수

```json
{
  "notification_type": "dispute_raised",
  "offer_id": "{offerId}",
  "proposal_id": "{proposalId}"
}
```

## 클릭 라우팅 기준

현재 백엔드는 명시적인 `deep_link`나 `target_page`를 내려주지 않는다. 클라이언트는 다음 값을 조합해 이동 대상을 결정한다.

- 1차 기준: `notification_type`
- 상세 조회 ID: `offer_id`
- 필요 시 상위 게시물 ID: `proposal_id`

동일한 `notification_type=meeting_confirmed`는 지원자 확인과 요청자 확인 모두에서 사용된다. 수신자 역할에 따라 화면 분기가 필요하면 클라이언트의 현재 사용자 역할 또는 Offer/Proposal 상세 조회 결과로 분기한다.

## 구현 주의사항

- `POST /v1/proposal/{proposalId}/confirm-received`에서 생성되는 알림은 현재 라우터에 즉시 발송 background task가 연결되어 있지 않다. 알림 레코드는 생성되지만 즉시 FCM 전송이 보장되지 않는다.
- 커스텀 알림 API 경로는 자동 알림과 달리 `notification_id`, `related_entity_type`, `related_entity_id`, `data_*` 필드를 포함할 수 있다. 이 문서는 자동 알림 outbox 발송 payload만 다룬다.
