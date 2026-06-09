# Mission API Removal Note

Mission API는 제거되었다.

현재 수행 흐름은 다음 API가 담당한다.

| 기능 | API |
|------|-----|
| Offer 수락 | `POST /v1/offer/{offerId}/accept` |
| 러너 전달 완료 | `POST /v1/offer/{offerId}/complete-delivery` |
| 러너 분쟁 접수 | `POST /v1/offer/{offerId}/dispute` |
| 오더 수령 확인 | `POST /v1/proposal/{proposalId}/confirm-received` |
| 오더 분쟁 접수 | `POST /v1/proposal/{proposalId}/dispute` |
| 관리자 정산 완료 | `POST /api/v1/admin/offer/{offerId}/confirm-settlement` |
| 관리자 환불 완료 | `POST /api/v1/admin/offer/{offerId}/refund` |

상태 정본은 Proposal/Offer이며, 배송 사진과 분쟁 사유는 Proof에 기록한다.
통합 명세는 [`../../api-spec/README.md`](../../api-spec/README.md), 도메인 기준은 [`../../domain.md`](../../domain.md)를 따른다.
