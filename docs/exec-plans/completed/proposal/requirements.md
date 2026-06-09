# Proposal Migration Requirements

## Current Policy

- Proposal은 오더가 작성하는 심부름 모집 공고다.
- 모든 Proposal API는 현재 Spring Security 설정상 JWT 인증이 필요하다.
- 공개 목록은 status 미지정 시 모든 Proposal 상태를 반환하고, 반복 `status` 쿼리로 여러 상태를 필터링한다.
- 생성 직후 상태는 `HOLDING`이며, 입금 확인 후 `POSTED`로 전환되어야 공개/입찰 대상이 된다.
- 현재 외부 API는 `title`, `content`, `deadline`, `errandFee` 중심으로 동작한다.
- `meetingAt`, `itemPrice`, `deposit`, 주소/좌표 필드는 현재 Java Proposal API/엔티티 응답에 포함되지 않는다.

## Target Policy

- FastAPI 구현은 현재 Java 구현과 같은 요청/응답/상태 코드/메시지/상태 전이를 유지한다.
- User/Auth에서 만든 current-user dependency와 공통 응답/에러 계약을 그대로 사용한다.
- Offer와의 연동은 현재 Proposal API가 요구하는 범위로 제한한다.

## In Scope

- `GET /v1/proposal`
- `GET /v1/proposal/{id}`
- `GET /v1/proposal/own`
- `POST /v1/proposal`
- `PUT /v1/proposal/{id}`
- `POST /v1/proposal/{id}/cancel`
- `ProposalStatus`
- 공개 조회 상태 필터
- 내 Proposal 조회 시 Offer 목록 포함
- 취소 시 WAITING Offer 자동 REJECTED 처리

## Out Of Scope

- 카테고리 API
- 주소/좌표 기반 Proposal
- `meetingAt`, `itemPrice`, `deposit` 외부 API 노출
- 관리자 입금 확인 API
- Proposal 자동 만료 배치
- Offer 생성/수락 API 자체 구현
- Mission 생성

## Acceptance Criteria

### `GET /v1/proposal`

- 인증된 사용자가 호출하면 200 OK와 PageResponse를 반환한다.
- `status` 쿼리가 없으면 모든 Proposal 상태를 반환한다.
- `status`는 반복 쿼리 파라미터로 여러 상태를 받을 수 있다. 예: `status=HOLDING&status=POSTED`
- `status` 쿼리가 있으면 해당 상태들만 반환한다.
- 토큰이 없거나 유효하지 않으면 401 `INVALID_TOKEN`이다.

### `GET /v1/proposal/{id}`

- 존재하는 `POSTED`, `OFFERED`, `MATCHED`, `CANCELLED` Proposal은 상세 응답을 반환한다.
- 존재하지 않는 Proposal은 404 `PROPOSAL_NOT_FOUND`다.
- `HOLDING` Proposal은 존재하더라도 404 `PROPOSAL_NOT_FOUND`로 숨긴다.

### `GET /v1/proposal/own`

- 현재 사용자가 작성한 Proposal만 반환한다.
- `status` 쿼리가 없으면 본인이 작성한 모든 Proposal 상태를 반환한다.
- `status`는 반복 쿼리 파라미터로 여러 상태를 받을 수 있다. 예: `status=HOLDING&status=POSTED`
- `status` 쿼리가 있으면 해당 상태들만 반환한다.
- 각 항목은 `offerCount`와 `offers`를 포함한다.
- `offers`는 생성 시각 내림차순이다.

### `POST /v1/proposal`

- 요청 필드는 `title`, `content`, `deadline`, `errandFee`다.
- `title`은 필수, 공백 불가, 50자 이하다.
- `content`는 필수, 공백 불가, 500자 이하다.
- `deadline`은 오프셋 포함 ISO-8601 문자열이어야 한다.
- 오프셋 없는 deadline은 400 `INVALID_DATE_TIME_FORMAT`이다.
- 과거 deadline은 400 `PROPOSAL_DEADLINE_INVALID`다.
- `errandFee`는 필수이며 1000원 이상이어야 한다.
- 성공 시 201 Created, 메시지 `요청이 등록되었습니다.`를 반환한다.
- 생성 상태는 `HOLDING`이다.

### `PUT /v1/proposal/{id}`

- 작성자 본인만 수정할 수 있다.
- `HOLDING`, `POSTED` 상태만 수정할 수 있다.
- `OFFERED`, `MATCHED`, `CANCELLED`는 409 `PROPOSAL_NOT_EDITABLE`이다.
- 존재하지 않는 Proposal은 404 `PROPOSAL_NOT_FOUND`다.
- 작성자가 아니면 403 `FORBIDDEN`이다.
- 성공 메시지는 `제안이 수정되었습니다.`다.

### `POST /v1/proposal/{id}/cancel`

- 작성자 본인만 취소할 수 있다.
- `HOLDING`, `POSTED`, `OFFERED` 상태만 취소할 수 있다.
- `MATCHED`, `CANCELLED`는 409 `PROPOSAL_NOT_CANCELLABLE`이다.
- `OFFERED` 상태 취소 시 연결된 `WAITING` Offer는 `REJECTED`가 된다.
- 이미 `CANCELLED`인 Offer는 유지된다.
- 성공 메시지는 `제안이 취소되었습니다.`다.
