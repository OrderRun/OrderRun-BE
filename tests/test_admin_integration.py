from __future__ import annotations

from app.models.mission import MissionStatus
from app.models.proposal import ProposalStatus

from tests.test_mission_integration import make_mission, make_user
from tests.test_proposal_integration import make_proposal


def test_confirm_payment_posts_holding_proposal_without_request_body(client, db, auth_headers, sample_user):
    proposal = make_proposal(db, sample_user.id, ProposalStatus.HOLDING)

    response = client.post(f"/api/v1/admin/proposal/{proposal.id}/confirm-payment", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "POSTED"
    db.refresh(proposal)
    assert proposal.status == ProposalStatus.POSTED


def test_confirm_payment_rejects_non_holding_proposal(client, db, auth_headers, sample_user):
    proposal = make_proposal(db, sample_user.id, ProposalStatus.POSTED)

    response = client.post(f"/api/v1/admin/proposal/{proposal.id}/confirm-payment", headers=auth_headers)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_STATUS"


def test_confirm_mission_settlement_sets_settled(client, db, auth_headers, sample_user):
    runner = make_user(db, "01066660001")
    mission, _ = make_mission(db, sample_user, runner, MissionStatus.COMPLETED)

    response = client.post(f"/api/v1/admin/mission/{mission.id}/confirm-settlement", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "SETTLED"
    assert response.json()["data"]["settledAt"] is not None
    db.refresh(mission)
    assert mission.status == MissionStatus.SETTLED
    assert mission.settled_at is not None


def test_confirm_mission_settlement_rejects_non_completed(client, db, auth_headers, sample_user):
    runner = make_user(db, "01066660002")
    mission, _ = make_mission(db, sample_user, runner, MissionStatus.DELIVERY_COMPLETED)

    response = client.post(f"/api/v1/admin/mission/{mission.id}/confirm-settlement", headers=auth_headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "MISSION_NOT_UPDATABLE"


def test_refund_mission_sets_refunded_from_disputed(client, db, auth_headers, sample_user):
    runner = make_user(db, "01066660003")
    mission, _ = make_mission(db, sample_user, runner, MissionStatus.DISPUTED)

    response = client.post(f"/api/v1/admin/mission/{mission.id}/refund", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "REFUNDED"
    db.refresh(mission)
    assert mission.status == MissionStatus.REFUNDED
