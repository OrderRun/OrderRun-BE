# OrderRun 도메인 정책 정본

이 문서는 API 명세에서 참조하는 도메인 상태와 정책 해석의 기준이다.
외부 API 요청/응답 계약은 [`api-spec/README.md`](./api-spec/README.md)를 우선한다.

## ProposalStatus

| 값 | 설명 |
|----|------|
| HOLDING | 입금 확인 대기 |
| POSTED | 모집 중 |
| OFFERED | 제안 도착 |
| MATCHED | 매칭 완료 |
| CANCELLED | 취소됨 |

## OfferStatus

| 값 | 설명 |
|----|------|
| WAITING | 수락 대기 |
| ACCEPTED | 수락됨 |
| COMPLETED | 수행 완료 |
| REJECTED | 거절됨 |
| CANCELLED | 취소됨 |

## MissionStatus

| 값 | 설명 |
|----|------|
| CREATED | Mission 생성 후 수행 시작 전 |
| IN_PROGRESS | 러너 수행 중 |
| DELIVERY_COMPLETED | 러너 전달 완료 및 인증 업로드 완료 |
| RECEIVED_CONFIRMED | 오더 수령 확인 완료 |
| COMPLETED | 전달 완료와 수령 확인이 모두 끝난 수행 완료 |
| SETTLED | 정산 완료 |
| DISPUTED | 분쟁 접수 |
| REFUNDED | 환불 완료 |

## 정책 기준

- Proposal은 모집 가능 상태에서 Offer를 받을 수 있고, Offer 수락 후 `MATCHED`가 된다.
- Offer 수락 시 선택된 Offer는 `ACCEPTED`, 같은 Proposal의 다른 대기 Offer는 `REJECTED`가 된다.
- Mission은 Offer 수락의 결과로 생성되며, 수행 시작, 전달 완료, 수령 확인, 정산, 분쟁/환불 흐름을 가진다.
- 정산 계좌와 약관 동의는 사용자 식별자에 종속된 사용자 부가 정책이다.
