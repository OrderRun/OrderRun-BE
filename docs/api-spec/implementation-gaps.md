# API 명세 구현 갭

이 문서는 [`README.md`](./README.md)의 정본 API 명세와 현재 FastAPI 구현 사이의 확인된 차이를 추적한다.
정본은 API 명세서이며, 아래 항목은 후속 구현 정렬 대상이다.

## 확인된 갭

| 영역 | 정본 | 현재 구현 관찰 | 후속 조치 |
|------|------|----------------|-----------|
| Settlement account encryption | 계좌번호는 응답에 노출하지 않음 | `encrypted_account_number` 컬럼에 현재 평문 저장 | 운영 전 KMS/암호화 유틸 연결 필요 |

## 점검 명령

```bash
rg -n "/api/v1|page=1|PENDING_PAYMENT|contractAmount|\\bitems\\b|\\btotal\\b" docs app tests
```

## 원칙

- 외부 계약 충돌 시 [`README.md`](./README.md)를 우선한다.
- 코드에서 이미 제공하는 호환 동작은 정본 명세에 맞게 이름, 상태 코드, 응답 래퍼를 정렬한다.
- 후속 구현 작업은 관련 통합 테스트를 먼저 추가하거나 갱신한 뒤 진행한다.
