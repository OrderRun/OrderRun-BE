# Offer Test Scenarios

기준 테스트 파일: `tests/test_offer_integration.py`

## 보장 범위

- Offer 생성은 `proposalId`만 입력으로 받고 Proposal을 `OFFERED`로 전이한다.
- 두 번째 Offer 생성은 Proposal을 `OFFERED`로 유지한다.
- 목록/내 목록 조회는 최신순 정렬, 페이징, 반복 `status` 필터를 지원한다.
- Proposal별 목록 조회는 상세 조회와 별도 DTO를 사용하며 오픈채팅방 링크를 반환하지 않는다.
- 상세 조회는 인증된 사용자에게 Offer 상태와 수락 이후 timestamp를 반환한다.
- 상세 조회는 수락 이후 상태에서 오더러와 해당 러너에게만 오픈채팅방 링크를 반환하고, 그 외에는 null을 반환한다.
- Offer 수락은 선택 Offer를 `ACCEPTED`, 같은 Proposal의 다른 대기 Offer를 `REJECTED`, Proposal을 `MATCHED`로 전이하고 수락 timestamp를 기록한다.
- 이미 활성 수락 Offer가 있으면 추가 수락을 막는다.
- 취소는 러너 본인과 `WAITING` 상태 규칙을 따른다.
- 러너 완료는 Offer를 `RUNNER_COMPLETED` 또는 `ALL_COMPLETED`로 전이하고 Proposal 상태와 동기화한다.
- 러너 분쟁은 active `RUNNER` 설문 질문 ID와 사유를 DisputeEvidence에 기록하고, `ACCEPTED` 또는 `RUNNER_COMPLETED`에서 Offer와 Proposal을 `DISPUTED`로 전이하고 timestamp를 기록한다.
- 러너 분쟁은 누락, 비활성, 대상 불일치 설문 질문 ID를 거절한다.
- 러너 분쟁은 `ALL_COMPLETED`에서 거절되며 상태와 timestamp를 유지한다.
- 러너 분쟁은 알림이 켜진 오더러에게 분쟁 알림을 생성한다.
- validation, 권한, 상태 오류는 정본 에러 계약을 따른다.
