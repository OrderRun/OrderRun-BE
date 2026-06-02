# Proposal Integration Test Plan

이 문서는 [`../../api-spec/README.md`](../../api-spec/README.md)의 Proposal API 계약을 검증하기 위한 통합 테스트 체크리스트다.

## 정상 시나리오

- `GET /v1/proposal`은 인증된 사용자에게 `200 OK`와 `ApiResponse<PageResponse<ProposalResponse>>`를 반환하고 반복 `status` 쿼리로 여러 상태를 필터링한다.
- `GET /v1/proposal/{id}`는 존재하는 Proposal에 대해 `ProposalDetailResponse`를 반환한다.
- `GET /v1/proposal/own`은 반복 `status`, `page`, `size`, `sort` 쿼리를 받아 `PageResponse<ProposalOwnResponse>`를 반환한다.
- `POST /v1/proposal`은 유효한 `title`, `content`, `deadline`, `errandFee`로 `201 Created`와 `ProposalResponse`를 반환한다.
- `PUT /v1/proposal/{id}`는 작성자만 수정할 수 있고 성공 시 `ProposalResponse`를 반환한다.
- `POST /v1/proposal/{id}/cancel`은 작성자만 취소할 수 있고 성공 시 취소된 `ProposalResponse`를 반환한다.

## 실패 시나리오

- 인증 토큰이 없거나 유효하지 않으면 `401` 계열 에러 응답을 반환한다.
- 존재하지 않는 Proposal은 `PROPOSAL_NOT_FOUND`를 반환한다.
- 작성자가 아닌 사용자의 수정/취소는 `FORBIDDEN`을 반환한다.
- 공백 제목/내용, 길이 초과, 과거 deadline, 1000원 미만 errandFee는 `VALIDATION_ERROR` 또는 정본 에러 코드를 반환한다.
- 수정 또는 취소 불가능한 상태에서는 `PROPOSAL_NOT_EDITABLE` 또는 `PROPOSAL_NOT_CANCELLABLE`을 반환한다.

## 응답 구조 검증

- 성공 응답은 `success=true`, `data`, `message` 구조를 따른다.
- 목록 응답은 `data.content`, `data.totalElements`, `data.totalPages`, `data.pageNumber`, `data.pageSize`, `data.first`, `data.last`를 포함한다.
- 실패 응답은 `success=false`, `error.code`, `error.message`, `error.details`, `timestamp` 구조를 따른다.

## 참고

- 통합 API 명세: [`../../api-spec/README.md`](../../api-spec/README.md)
- 구현 갭 점검: [`../../api-spec/implementation-gaps.md`](../../api-spec/implementation-gaps.md)
