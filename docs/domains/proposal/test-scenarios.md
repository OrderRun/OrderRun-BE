# Proposal Test Scenarios

기준 테스트 파일: `tests/test_proposal_integration.py`

## 보장 범위

- 공개 Proposal 목록은 인증을 요구하고 `POSTED/OFFERED` 상태만 반환하며 반복 `status` 쿼리로 이를 필터링한다.
- 공개 Proposal 목록은 `deadline`이 빠른 순서로 반환하고, 동률이면 최신 생성 항목을 우선한다.
- 상세 조회는 Proposal 상태와 무관하게 존재하는 요청을 반환하며, 매칭 이후 상태 timestamp를 노출한다.
- 상세 조회는 매칭 이후 상태에서 오더러와 수락된 러너에게만 오픈채팅방 링크를 반환하고, 그 외에는 null을 반환한다.
- 내 Proposal 목록은 현재 사용자 요청만 반환하고 연결된 Offer 요약과 다중 상태 필터를 포함하며, `deadline`이 빠른 순서로 반환한다.
- 생성은 계약 필드와 validation을 검증하고 초기 상태를 `HOLDING`으로 저장한다.
- 수정과 취소는 작성자 권한, 상태 규칙, 대기 Offer 정리 규칙을 검증한다.
- 오더러 수령 확인은 Proposal을 `ORDER_COMPLETED` 또는 `ALL_COMPLETED`로 전이하고 Offer 상태와 동기화한다.
- 오더러 분쟁 접수는 active `ORDER` 설문 질문 ID와 사유를 Proof에 기록하고, `MATCHED` 또는 `ORDER_COMPLETED`에서 Proposal과 수락된 Offer를 `DISPUTED`로 전이하고 timestamp를 기록한다.
- 오더러 분쟁 접수는 누락, 비활성, 대상 불일치 설문 질문 ID를 거절한다.
- 오더러 분쟁 접수는 `ALL_COMPLETED`에서 거절되며 상태와 timestamp를 유지한다.
- 오더러 분쟁 접수는 알림이 켜진 러너에게 분쟁 알림을 생성한다.
- 게시글 신고는 다른 사용자의 공개 모집 상태 Proposal에 한해 사유 항목과 선택 상세 사유로 생성하며, 사용자당 게시글별 한 건만 허용한다.
- 관리자 신고 승인은 Proposal을 `REPORTED`로 전환하고 대기 Offer를 거절하며 공개 목록에서 제외한다. 반려는 Proposal 상태를 바꾸지 않고 신고 이력을 유지한다.
- ORM 모델 계약은 문서화된 필드와 enum 정책이 구현에 남아 있는지 확인한다.
