# OrderRun API 계약

이 문서는 API 계약 문서의 레거시 진입점이다.

현재 외부 API 요청/응답 계약의 정본은 [`../api-spec/README.md`](../api-spec/README.md)다.
도메인 상태와 정책 해석은 [`../domain.md`](../domain.md)를 우선한다.

## 정본 규칙

- Base URL은 `/v1`이다.
- 성공 응답은 `ApiResponse<T>`를 사용한다. 단, `DELETE /v1/offer/{offerId}`는 `204 No Content`와 빈 본문을 반환한다.
- 페이징 응답은 `PageResponse<T>`를 `data`에 담는다.
- 실패 응답은 `success=false`, `error`, `timestamp` 구조를 사용한다.

## 관련 문서

- [통합 API 명세](../api-spec/README.md)
- [구현 갭 점검](../api-spec/implementation-gaps.md)
- [도메인 정책 정본](../domain.md)
