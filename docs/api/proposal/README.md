# Proposal API

이 디렉터리는 Proposal 관련 과거 상세 문서 위치를 유지한다.
외부 API 요청/응답 계약의 정본은 [`../../api-spec/README.md`](../../api-spec/README.md)의 `Proposal API` 섹션이다.

## 문서 목록

- [`proposal-api-spec.md`](./proposal-api-spec.md): 통합 API 명세 참조
- [`proposal-entity.md`](./proposal-entity.md): Proposal 도메인 정책 참조
- [`proposal-integration-test-plan.md`](./proposal-integration-test-plan.md): 정본 기준 통합 테스트 체크리스트

## API 엔드포인트 요약

| Method | Path | 설명 | 인증 |
|--------|------|------|------|
| GET | `/v1/proposal` | 요청 게시글 목록 조회 | 필요 |
| GET | `/v1/proposal/{id}` | 요청 게시글 상세 조회 | 필요 |
| GET | `/v1/proposal/own` | 내 요청 게시글 목록 조회 | 필요 |
| POST | `/v1/proposal` | 요청 게시글 등록 | 필요 |
| PUT | `/v1/proposal/{id}` | 요청 게시글 수정 | 필요. 작성자만 가능 |
| POST | `/v1/proposal/{id}/cancel` | 요청 게시글 취소 | 필요. 작성자만 가능 |

## 관련 문서

- [통합 API 명세](../../api-spec/README.md)
- [도메인 정책 정본](../../domain.md)
- [구현 갭 점검](../../api-spec/implementation-gaps.md)
