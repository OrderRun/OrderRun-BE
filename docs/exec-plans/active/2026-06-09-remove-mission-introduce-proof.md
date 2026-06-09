# Mission 제거와 Proof 도입 계획

## 목표

Mission을 제거하고 수락된 Offer를 수행 건 기준으로 사용한다.
Proposal/Offer는 각 역할의 상태와 상태별 시각을 직접 보유하고, 배송 사진과 분쟁 사유는 Proof 엔티티에 기록한다.

## 범위

- Mission 모델, 서비스, 응답, 일반/관리자 API 제거
- Proof 모델, 스키마, migration 추가
- Proposal/Offer 상태별 timestamp 컬럼 추가
- Offer ID 기준 수락, 배송 완료, 분쟁, 관리자 정산/환불 흐름 전환
- Proposal ID 기준 오더 수령 확인, 오더 분쟁 흐름 전환
- API Spec, Domain Spec, generated schema, 관련 테스트 갱신

## 비범위

- 결제/정산 계좌 도메인 재설계
- Proof 조회 API 추가
- 파일 업로드 저장소 구현
- 기존 운영 데이터의 완전한 downgrade 복원

## 가정

- 수락된 Offer ID가 수행 건의 기준 식별자다.
- Proposal에 `acceptedOfferId` 컬럼은 추가하지 않는다.
- Proof는 증빙성 기록만 담당한다.
- 정산 완료는 Proof가 아니라 Proposal/Offer timestamp로 기록한다.

## 작업 분해

1. [x] Domain/API Spec을 Mission 제거와 Proof 기준으로 갱신한다.
2. [x] Proposal/Offer timestamp 컬럼과 Proof 모델/migration을 추가하고 Mission 모델을 제거한다.
3. [x] Offer/Proposal/Admin 서비스와 라우터를 Mission 없이 동작하도록 전환한다.
4. [x] 테스트를 Proof 생성, timestamp 기록, Mission API 제거 기준으로 재구성한다.
5. [x] 문서와 generated schema에서 Mission 잔여 참조를 정리한다.

## 검증 전략

- 각 단계 후 `rg`로 Mission 잔여 참조를 확인한다.
- 핵심 전환 후 `python -m compileall app`를 실행한다.
- API 계약 변경 후 `pytest tests/test_openapi.py`를 실행한다.
- 최종적으로 `pytest` 전체를 실행한다.

## 현재 검증 기록

- `python -m compileall app tests`
- `pytest tests/test_offer_integration.py tests/test_proposal_integration.py`
- `pytest tests/test_mission_integration.py tests/test_admin_integration.py tests/test_openapi.py`

## 롤아웃 또는 롤백 메모

- migration은 기존 missions 데이터를 Proof와 Proposal/Offer timestamp로 이관한 뒤 missions를 삭제한다.
- downgrade는 missions 테이블 재생성과 timestamp 컬럼 제거까지만 지원하며 Proof 이력의 완전 복원은 보장하지 않는다.

## 남은 리스크

- 기존 클라이언트가 `missionId`를 사용 중이면 breaking change다.
- 기존 DB에 Mission 없이 진행 상태가 꼬인 데이터가 있으면 이관 품질이 데이터 상태에 의존한다.
- 알림 타입이 `execution_started`, `execution_completed`로 바뀌므로 클라이언트 알림 필터/딥링크 확인이 필요하다.
