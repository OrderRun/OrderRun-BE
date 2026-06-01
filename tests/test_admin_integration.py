from __future__ import annotations

from app.models.proposal import ProposalStatus

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
