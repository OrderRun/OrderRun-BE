# Mission Verification Superseded

Mission 제거 후 검증 기준:
- `/v1/mission/...` API가 404를 반환한다.
- Offer 수락 응답에 `missionId`가 없다.
- Proposal/Offer 상세 응답에 역할별 timestamp가 포함된다.
- 배송 완료와 분쟁 접수 시 Proof가 생성된다.
- 관리자 정산/환불은 `/api/v1/admin/offer/{offerId}/...`를 사용한다.

대표 테스트:
- `pytest tests/test_mission_integration.py`
- `pytest tests/test_offer_integration.py`
- `pytest tests/test_proposal_integration.py`
- `pytest tests/test_admin_integration.py`
- `pytest tests/test_openapi.py`
