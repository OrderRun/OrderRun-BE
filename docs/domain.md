# OrderRun 도메인 정책 정본

이 문서는 API 명세에서 참조하는 도메인 상태와 정책 해석의 기준이다.
외부 API 요청/응답 계약은 [`api-spec/README.md`](./api-spec/README.md)를 우선한다.

## ProposalStatus

Proposal은 오더 관점의 모집 및 수행 상태를 추적한다.

| 값 | 설명 |
|----|------|
| HOLDING | 입금 확인 대기 |
| POSTED | 모집 중 |
| OFFERED | 제안 도착 |
| MATCHED | Offer 수락으로 수행 건이 확정된 상태 |
| ORDER_COMPLETED | 오더러가 완료 확인을 마친 상태 |
| ALL_COMPLETED | 러너와 오더러가 모두 완료 확인을 마친 상태 |
| DISPUTED | 분쟁 접수 |
| RESOLVED | 분쟁 해결 완료 |
| CANCELLED | 매칭 전 취소됨 |

### Proposal 상태 전이

| 전이 | 발생 시점 |
|------|-----------|
| `HOLDING -> POSTED` | 입금 또는 관리자 확인으로 모집이 공개될 때 |
| `POSTED -> OFFERED` | 첫 Offer가 생성될 때 |
| `OFFERED -> MATCHED` | 오더가 Offer 하나를 수락할 때 |
| `MATCHED -> ORDER_COMPLETED` | 오더러가 Proposal에서 완료를 확인할 때 |
| `ORDER_COMPLETED + Offer RUNNER_COMPLETED -> ALL_COMPLETED` | 러너와 오더러 완료가 모두 접수될 때 |
| `MATCHED/ORDER_COMPLETED -> DISPUTED` | 오더 또는 러너가 분쟁을 접수할 때 |
| `DISPUTED -> RESOLVED` | 분쟁 처리가 완료될 때 |
| `HOLDING/POSTED/OFFERED -> CANCELLED` | 오더가 매칭 전 Proposal을 취소할 때 |

## OfferStatus

Offer는 러너 관점의 제안 및 수행 상태를 추적한다.

| 값 | 설명 |
|----|------|
| WAITING | 수락 대기 |
| ACCEPTED | 수락되어 수행 건 기준이 된 상태 |
| RUNNER_COMPLETED | 러너가 완료와 증빙 업로드를 마친 상태 |
| ALL_COMPLETED | 러너와 오더러가 모두 완료 확인을 마친 상태 |
| DISPUTED | 분쟁 접수 |
| RESOLVED | 분쟁 해결 완료 |
| REJECTED | 거절됨 |
| CANCELLED | 러너가 수락 전 취소함 |

### Offer 상태 전이

| 전이 | 발생 시점 |
|------|-----------|
| `WAITING -> ACCEPTED` | 오더가 해당 Offer를 수락할 때 |
| `ACCEPTED -> RUNNER_COMPLETED` | 러너가 Offer에서 완료를 등록할 때 |
| `RUNNER_COMPLETED + Proposal ORDER_COMPLETED -> ALL_COMPLETED` | 러너와 오더러 완료가 모두 접수될 때 |
| `ACCEPTED/RUNNER_COMPLETED -> DISPUTED` | 오더 또는 러너가 분쟁을 접수할 때 |
| `DISPUTED -> RESOLVED` | 분쟁 처리가 완료될 때 |
| `WAITING -> REJECTED` | 같은 Proposal의 다른 Offer가 수락되거나 Proposal 취소로 대기 Offer가 정리될 때 |
| `WAITING -> CANCELLED` | 러너가 수락 전 Offer를 취소할 때 |

## Proof

Proof는 수행 과정에서 남기는 증빙성 기록이다.
수행 상태의 정본은 Proposal/Offer이며, Proof는 사진 또는 사유 같은 근거를 보관한다.

| ProofType | 설명 |
|-----------|------|
| DELIVERY | 러너 완료 증빙 |
| DISPUTE | 오더 또는 러너의 분쟁 사유 |

Proof는 `proposalId`, `offerId`, `actorId`, `proofType`, `imageUrl`, `reason`, `surveyQuestionId`, `createdAt`을 가진다.

## 정책 기준

- Proposal은 모집 가능 상태에서 Offer를 받을 수 있고, Offer 수락 후 `MATCHED`가 된다.
- Offer 수락 시 선택된 Offer는 `ACCEPTED`, 같은 Proposal의 다른 대기 Offer는 `REJECTED`가 된다.
- 수락된 Offer ID가 매칭 이후 수행 건의 기준 식별자다.
- 매칭 이후 오더 관점 진행 상태는 Proposal, 러너 관점 진행 상태는 Offer에서 추적한다.
- 완료 증빙과 분쟁 사유 및 선택한 분쟁 설문 질문 ID는 Proof에 기록한다.
- 정산 계좌와 약관 동의는 사용자 식별자에 종속된 사용자 부가 정책이다.
