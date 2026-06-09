# 문서 하네스 보수적 정리 계획

## 목표

`docs/exec-plans/active/`에는 실제 진행 중인 계획만 남기고, 완료되었거나 대체된 실행 계획은 `docs/exec-plans/completed/`로 보관한다.

## 범위

- 완료된 Mission 제거/Proof 도입 계획 보관
- 구현 완료 또는 기준 문서화가 끝난 도메인 마이그레이션 계획 묶음 보관
- Mission으로 대체된 실행 계획 묶음 보관
- active/completed 인덱스와 관련 링크 갱신
- 남은 레거시 문서 통합 부채 기록

## 비범위

- 앱 코드 변경
- 테스트 코드 변경
- `docs/api-spec/`, `docs/domain.md`, `docs/architecture/`, `docs/api/`, `docs/offer/` 통합 또는 삭제
- 생성 문서 재생성 자동화 추가

## 가정

- `2026-06-02-firebase-config-integration.md`는 `Status: PLANNED`이고 보안 이슈를 포함하므로 active에 유지한다.
- 보수적 정리 원칙에 따라 문서 내용은 삭제하지 않고 보관 위치로 이동한다.
- 파생 문서인 `docs/generated/db-schema.md`는 이번 정리에서 링크만 새 위치에 맞춘다.

## 작업 분해

1. [x] 완료/대체 실행 계획을 `completed/`로 이동한다.
2. [x] `active/README.md`와 `completed/README.md`를 현재 상태에 맞게 갱신한다.
3. [x] 이동으로 깨지는 문서 링크를 갱신한다.
4. [x] 후속 문서 통합 부채를 `tech-debt-tracker.md`에 기록한다.
5. [ ] `rg`와 `find`로 active 잔여 참조와 파일 위치를 확인한다.

## 검증 전략

- `find docs/exec-plans -type f | sort`
- `rg -n "docs/exec-plans/active/(user-auth|proposal|offer|terms-agreement|mission|2026-06-09-remove-mission)" . -g '*.md'`
- `rg -n "active/(user-auth|proposal|offer|terms-agreement|mission|2026-06-09-remove-mission)" docs -g '*.md'`
- `git status --short`

## 남은 리스크

- `docs/architecture/`와 도메인별 레거시 API 문서는 여전히 정본 문서와 중복된다.
- `docs/generated/db-schema.md`는 생성 문서지만 수동 링크 정렬만 수행하므로, 이후 실제 재생성 절차가 필요할 수 있다.
