# 하네스 엔지니어링 시작 가이드

## 이 문서는 무엇인가요?

OrderRun-BE는 **하네스 엔지니어링(Harness Engineering)** 방법론을 사용합니다.
이것은 코드보다 문서를 먼저 작성하여, AI Agent든 인간이든 일관되고 예측 가능하게 시스템을 발전시키는 접근법입니다.

## 5분 빠른 시작

### 1단계: 진입점 확인

작업을 시작하기 전에 다음 문서를 읽으세요:

1. **[README.md](../README.md)** - 프로젝트 개요
2. **[AGENTS.md](../AGENTS.md)** - AI Agent 작업 규칙
3. **[ARCHITECTURE.md](../ARCHITECTURE.md)** - 시스템 지도

### 2단계: 작업 유형 파악

당신의 작업은 어떤 유형인가요?

| 작업 유형 | 먼저 확인할 문서 | 작성/갱신할 문서 |
|---------|---------------|---------------|
| 새 기능 추가 | `docs/product-specs/` | 제품 스펙 → 실행 계획 |
| 도메인 동작 변경 | `docs/domains/`, `docs/domain.md` | 도메인 문서 → 실행 계획 |
| 아키텍처 변경 | `docs/design-docs/` | 설계 문서 → 실행 계획 |
| 버그 수정 | `docs/exec-plans/tech-debt-tracker.md` | 실행 계획 (크기에 따라) |
| 리팩토링 | `docs/design-docs/` | 설계 문서 → 실행 계획 |

### 3단계: 문서 작성 또는 확인

**새 기능인 경우:**

```bash
# 1. 제품 스펙 작성
docs/product-specs/my-new-feature.md

# 2. 실행 계획 작성
docs/exec-plans/active/2026-03-25-my-new-feature.md

# 3. 코드 구현
app/...

# 4. 검증 후 계획 이동
docs/exec-plans/completed/2026-03-25-my-new-feature.md
```

**기존 기능 변경인 경우:**

```bash
# 1. 관련 문서 찾기
grep -r "기능 이름" docs/

# 2. 문서 갱신
vim docs/product-specs/existing-feature.md

# 3. 실행 계획 작성 (복잡하면)
docs/exec-plans/active/2026-03-25-update-feature.md

# 4. 코드 구현

# 5. 문서와 코드 일치 확인
```

### 4단계: 완료 전 체크리스트

- [ ] 관련 문서가 존재하고 최신 상태인가?
- [ ] 실행 계획의 검증 기준을 충족했는가?
- [ ] 품질 점수 평가표에서 모든 항목이 3점 이상인가?
- [ ] 남은 리스크가 부채 트래커에 기록되었는가?

## 핵심 문서 가이드

### 필독 문서 (이것만은 꼭!)

1. **[HARNESS_ENGINEERING.md](./HARNESS_ENGINEERING.md)**
   - 하네스 엔지니어링의 핵심 원칙
   - 작업 흐름 프로세스 (진입 → 계획 → 실행 → 검증 → 완료)
   - AI Agent 활용 가이드라인

2. **[DIRECTORY_STRUCTURE.md](./DIRECTORY_STRUCTURE.md)**
   - 어디에 어떤 파일을 둘지 결정
   - 각 디렉토리의 책임과 용도
   - 파일 배치 결정 트리

3. **[QUALITY_SCORE.md](./QUALITY_SCORE.md)**
   - 완료 기준 평가표
   - 머지 전 확인 사항

### 작업별 가이드

**설계 작업 시:**
- [DESIGN.md](./DESIGN.md) - 설계 문서 작성 규칙
- `docs/design-docs/index.md` - 기존 설계 문서 카탈로그

**계획 작업 시:**
- [PLANS.md](./PLANS.md) - 실행 계획 템플릿
- `docs/exec-plans/active/README.md` - 진행 중인 계획 목록

**도메인/테스트 보장 확인 시:**
- `docs/domains/README.md` - 도메인별 개념과 테스트 보장 문서
- [domain.md](./domain.md) - 상태 전이와 정책 정본
- [api-spec/README.md](./api-spec/README.md) - 외부 API 계약 정본

**보안/신뢰성 작업 시:**
- [SECURITY.md](./SECURITY.md) - 보안 체크리스트
- [RELIABILITY.md](./RELIABILITY.md) - 신뢰성 기준

### 반복 개선 참여

**[ITERATION_FRAMEWORK.md](./ITERATION_FRAMEWORK.md)**
- 주간 리뷰 (매주 월요일 권장)
- 월간 감사 (매월 첫째 주 권장)
- 분기별 회고 (분기 첫째 주 권장)

## 일반적인 시나리오

### 시나리오 1: 완전히 새로운 기능 추가

```
1. docs/product-specs/new-feature.md 작성
   → 사용자 관점에서 기능 정의

2. docs/design-docs/new-feature-design.md 작성 (필요시)
   → 기술적 결정 근거

3. docs/exec-plans/active/2026-XX-XX-new-feature.md 작성
   → 작업 분해, 검증 전략

4. 코드 구현
   → app/ 아래 적절한 위치

5. 검증
   → 계획 문서의 검증 기준 충족

6. 문서 갱신
   → 생성 문서 (스키마, API) 갱신

7. 계획 이동
   → exec-plans/active/ → completed/
```

### 시나리오 2: 기존 코드 리팩토링

```
1. docs/design-docs/에서 관련 설계 문서 확인
   → 기존 의도 파악

2. docs/design-docs/refactoring-rationale.md 작성
   → 왜 리팩토링하는가?
   → 어떻게 개선되는가?

3. docs/exec-plans/active/2026-XX-XX-refactoring.md 작성
   → 단계별 계획
   → 각 단계의 검증 방법

4. 작은 단위로 리팩토링 실행
   → 각 단계 후 검증

5. 설계 문서 갱신
   → 새로운 구조 반영

6. 계획 이동
   → exec-plans/active/ → completed/
```

### 시나리오 3: 긴급 버그 수정

```
작은 버그 (1파일, 10줄 이내):
→ 실행 계획 없이 즉시 수정
→ 커밋 메시지에 근거 명시

큰 버그 (여러 파일, 복잡한 로직):
1. docs/exec-plans/active/2026-XX-XX-bug-fix.md 작성
   → 문제 정의
   → 원인 분석
   → 수정 계획
   → 검증 전략

2. 수정 실행

3. 검증

4. 관련 문서 갱신 (설계/스펙)

5. 부채 트래커에 근본 원인 기록 (필요시)
```

### 시나리오 4: AI Agent와 협업

**Agent에게 요청하기 전:**

```markdown
# 나쁜 요청
"사용자 인증 기능 만들어줘"

# 좋은 요청
"docs/product-specs/user-authentication.md 스펙에 따라
사용자 인증 API를 구현해줘. 먼저
docs/exec-plans/active/2026-XX-XX-auth-implementation.md에
실행 계획을 작성하고, 계획에 따라 단계별로 진행해줘."
```

**Agent가 작업 중:**

```
1. Agent가 계획 문서 작성
   → 검토하고 피드백

2. Agent가 단계별 구현
   → 각 단계 완료 후 확인

3. Agent가 검증 수행
   → 검증 기준 충족 확인

4. Agent가 문서 갱신
   → 최종 검토
```

**Agent 독립성:**
- Claude Code, Cursor, GitHub Copilot 등 어떤 Agent든 동일한 문서 구조 사용
- Agent가 바뀌어도 문서만 보면 컨텍스트 복원 가능

## 자주 묻는 질문 (FAQ)

### Q1: 모든 작업에 문서가 필요한가요?

**A:** 크기에 따라 다릅니다.

- **1줄 수정, 오타 수정** → 문서 불필요, 커밋 메시지로 충분
- **단일 파일, 10줄 이내 변경** → 실행 계획 불필요, 관련 문서 갱신만
- **3단계 이상, 여러 파일 변경** → 실행 계획 필수
- **새 기능, 아키텍처 변경** → 제품 스펙 + 설계 문서 + 실행 계획 필요

### Q2: 문서 작성에 시간이 너무 오래 걸려요

**A:** 템플릿을 활용하고 최소 필수 항목만 작성하세요.

- 계획 문서: 목표, 작업 분해, 검증 전략만 (5-10분)
- 설계 문서: 문제 정의, 결정 내용, 리스크만 (10-15분)
- 시간이 오래 걸린다면 너무 상세하게 쓰고 있는 것

### Q3: 문서와 코드가 불일치하면 어떻게 하나요?

**A:** 코드가 맞다면 문서를 먼저 갱신하세요.

```
1. 왜 불일치가 생겼는지 파악
2. 문서를 코드에 맞게 갱신
3. 불일치가 반복되면 프로세스 개선
```

### Q4: 레거시 코드는 어떻게 하나요?

**A:** 점진적으로 문서화하세요.

- 새로 추가/변경하는 부분만 문서 작성
- 기존 코드는 건드릴 때 문서 추가
- 한 번에 전체 문서화 시도하지 말 것

### Q5: 실험적인 코드는 어떻게 관리하나요?

**A:** `docs/study/` 또는 별도 브랜치에서 실험하세요.

```
1. 실험 목적과 가설을 간단히 기록
2. docs/study/experiment-name.md에 결과 정리
3. 성공하면 정식 문서로 승격
4. 실패하면 학습 내용만 남기고 코드 삭제
```

### Q6: 팀원이 문서를 안 읽으면 어떻게 하나요?

**A:** 프로세스에 강제하세요.

- PR 템플릿에 "관련 문서 링크" 필드 추가
- CI에서 문서 링크 존재 여부 검증
- 문서 없는 PR은 리뷰 거부
- 주간 리뷰에서 문서 있는 PR 비율 공유

## 다음 단계

### 초보자 (첫 1주)

1. [ ] README.md, AGENTS.md, ARCHITECTURE.md 읽기
2. [ ] HARNESS_ENGINEERING.md 핵심 원칙 이해
3. [ ] 작은 작업 하나를 문서와 함께 완료해보기
4. [ ] 주간 리뷰 템플릿 확인

### 중급자 (첫 1개월)

1. [ ] 모든 상위 가이드 문서 정독
2. [ ] 실행 계획을 작성하며 복잡한 작업 완료
3. [ ] 설계 문서 1개 이상 작성
4. [ ] 주간 리뷰 참여 또는 주도

### 고급자 (지속적)

1. [ ] 월간 감사 주도
2. [ ] 분기별 회고 참여
3. [ ] 하네스 개선 실험 제안
4. [ ] 다른 팀원 온보딩 지원

## 참고 자료

### 핵심 가이드
- [HARNESS_ENGINEERING.md](./HARNESS_ENGINEERING.md)
- [DIRECTORY_STRUCTURE.md](./DIRECTORY_STRUCTURE.md)
- [ITERATION_FRAMEWORK.md](./ITERATION_FRAMEWORK.md)

### 작업 가이드
- [DESIGN.md](./DESIGN.md)
- [PLANS.md](./PLANS.md)
- [QUALITY_SCORE.md](./QUALITY_SCORE.md)

### 시스템 문서
- [ARCHITECTURE.md](../ARCHITECTURE.md)
- [AGENTS.md](../AGENTS.md)

## 도움이 필요하세요?

1. **문서 구조 질문** → DIRECTORY_STRUCTURE.md 참조
2. **작업 프로세스 질문** → HARNESS_ENGINEERING.md 참조
3. **품질 기준 질문** → QUALITY_SCORE.md 참조
4. **그 외** → AGENTS.md의 "운영 원칙" 섹션 참조

## 버전 이력

- 2026-03-25: 초안 작성
