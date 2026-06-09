# 설계 문서 인덱스

## 목적

이 폴더는 백엔드의 기술 설계와 장기적으로 유지할 의사결정 근거를 담는다.

## 현재 문서

- [`core-beliefs.md`](./core-beliefs.md): 아키텍처 선택을 이끄는 핵심 신념
- [`persistence-schema-canonicalization.md`](./persistence-schema-canonicalization.md): 전체 영속성 스키마 정본화와 현재 구현 갭
- [`testing-conventions.md`](./testing-conventions.md): pytest 통합 테스트 작성 규칙 (이름, GWT 구조, 중복 방지)
- [`../api-spec/README.md`](../api-spec/README.md): 외부 API 요청/응답 계약 정본
- [`../domain.md`](../domain.md): 도메인 상태와 정책 정본

## 다음 후보 문서

- 인증 전략
- 결제 제공자 추상화
- 운영 감사 로그
- 백그라운드 작업과 비동기 처리
