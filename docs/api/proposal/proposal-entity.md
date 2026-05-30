# Proposal Entity

Proposal 도메인 상태와 정책 해석의 정본은 [`../../domain.md`](../../domain.md)다.
외부 API 응답 필드는 [`../../api-spec/README.md`](../../api-spec/README.md)의 `ProposalResponse`, `ProposalOwnResponse`, `ProposalDetailResponse`를 우선한다.

## 정본 필드 요약

| 필드 | 설명 |
|------|------|
| `id` | Proposal ID |
| `ordererId` | 작성자 사용자 ID. 내 요청 게시글 응답에 포함 |
| `title` | 공고 제목 |
| `content` | 요청 상세 내용 |
| `deadline` | 수행 마감 시각 |
| `errandFee` | 심부름비 |
| `status` | `HOLDING`, `POSTED`, `OFFERED`, `MATCHED`, `CANCELLED` |
| `offerCount` | 연결된 Offer 개수. 내 요청 게시글 응답에 포함 |
| `offers` | 연결된 Offer 요약 목록. 내 요청 게시글 응답에 포함 |
| `createdAt` | 생성 시각. 내 요청 게시글 응답에 포함 |
| `updatedAt` | 수정 시각. 내 요청 게시글 응답에 포함 |

## 상태 요약

| 값 | 설명 |
|----|------|
| HOLDING | 입금 확인 대기 |
| POSTED | 모집 중 |
| OFFERED | 제안 도착 |
| MATCHED | 매칭 완료 |
| CANCELLED | 취소됨 |

## 참고

- 통합 API 명세: [`../../api-spec/README.md`](../../api-spec/README.md)
- 도메인 정책 정본: [`../../domain.md`](../../domain.md)
- 구현 갭 점검: [`../../api-spec/implementation-gaps.md`](../../api-spec/implementation-gaps.md)
