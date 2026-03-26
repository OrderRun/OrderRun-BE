# Proposal API

`Proposal` 도메인의 엔티티 정의, API 스펙, 통합 테스트 기준 문서를 모아둔 디렉터리입니다.

## 문서 목록

### 1. [proposal-entity.md](./proposal-entity.md)
엔티티 필드와 상태 규칙을 정의합니다.
- 필드 정의 및 제약조건
- 상태(Status) 정의 및 전이 규칙
- 비즈니스 규칙
- 관계(Relationship) 정의

### 2. [proposal-api-spec.md](./proposal-api-spec.md)
전체 조회, 상세 조회, 생성 API 스펙을 정의합니다.
- API 엔드포인트 정의
- 요청/응답 스키마
- 에러 코드 정의
- 유효성 검증 규칙

### 3. [proposal-integration-test-plan.md](./proposal-integration-test-plan.md)
통합 테스트 시나리오와 검증 포인트를 정의합니다.
- 정상 시나리오
- 실패 시나리오
- 검증 포인트
- 테스트 데이터 준비

## API 엔드포인트 요약

| Method | Path | 설명 | 인증 |
|--------|------|------|------|
| GET | `/api/v1/proposal` | 전체 제안 목록 조회 | 불필요 |
| GET | `/api/v1/proposal/{id}` | 특정 제안 상세 조회 | 불필요 |
| POST | `/api/v1/proposal` | 새 제안 생성 | 필요 |

## 상태(Status) 요약

- `POSTED`: 등록됨 (초기 상태)
- `OFFERED`: 제안 접수됨
- `MATCHED`: 매칭 완료
- `CANCELLED`: 취소됨

## 구현 순서

1. ✅ **문서 작성** (현재 단계)
2. ⏳ **테스트 작성** (다음 단계)
3. ⏳ **구현**
   - Proposal 엔티티 모델
   - Proposal 스키마 (Pydantic)
   - Proposal 서비스
   - Proposal API 라우터
4. ⏳ **테스트 실행 및 디버깅**

## 관련 문서

- [OrderRun Domain Model](../../architecture/orderrun-domain-model.md)
- [OrderRun API Contract](../../architecture/orderrun-api-contract.md)
