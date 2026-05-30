# Offer API Spec

Offer API의 외부 계약 정본은 [`../api-spec/README.md`](../api-spec/README.md)의 `Offer API` 섹션이다.

이 문서는 과거 도메인별 상세 명세 위치를 유지하기 위한 참조 문서다. 새 요청/응답 필드, 상태 코드, 페이징 규칙은 통합 API 명세를 우선한다.

## 포함 API

- `POST /v1/offer`
- `POST /v1/offer/{offerId}/accept`
- `GET /v1/offer/{offerId}`
- `GET /v1/offer?proposalId={id}`
- `GET /v1/offer/own`
- `DELETE /v1/offer/{offerId}`

## 참고

- 상태 정책: [`../domain.md`](../domain.md)
- 구현 갭: [`../api-spec/implementation-gaps.md`](../api-spec/implementation-gaps.md)
