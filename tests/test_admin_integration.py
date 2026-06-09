from __future__ import annotations

from app.models.offer import OfferStatus
from app.models.proposal import Proposal, ProposalStatus

from tests.test_mission_integration import make_execution, make_user
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


def test_confirm_offer_settlement_sets_settled(client, db, auth_headers, sample_user):
    runner = make_user(db, "01066660001")
    proposal, offer = make_execution(
        db,
        sample_user,
        runner,
        ProposalStatus.RECEIVED_CONFIRMED,
        OfferStatus.RECEIPT_CONFIRMED,
    )

    response = client.post(f"/api/v1/admin/offer/{offer.id}/confirm-settlement", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "SETTLED"
    assert response.json()["data"]["settledAt"] is not None
    db.refresh(proposal)
    db.refresh(offer)
    assert proposal.status == ProposalStatus.SETTLED
    assert offer.status == OfferStatus.SETTLED
    assert proposal.settled_at is not None
    assert offer.settled_at is not None


def test_confirm_offer_settlement_rejects_non_completed(client, db, auth_headers, sample_user):
    runner = make_user(db, "01066660002")
    _, offer = make_execution(db, sample_user, runner, ProposalStatus.DELIVERY_REPORTED, OfferStatus.DELIVERY_COMPLETED)

    response = client.post(f"/api/v1/admin/offer/{offer.id}/confirm-settlement", headers=auth_headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "OFFER_NOT_UPDATABLE"


def test_refund_offer_sets_refunded_from_disputed(client, db, auth_headers, sample_user):
    runner = make_user(db, "01066660003")
    proposal, offer = make_execution(db, sample_user, runner, ProposalStatus.DISPUTED, OfferStatus.DISPUTED)

    response = client.post(f"/api/v1/admin/offer/{offer.id}/refund", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "REFUNDED"
    assert response.json()["data"]["refundedAt"] is not None
    db.refresh(proposal)
    db.refresh(offer)
    assert proposal.status == ProposalStatus.REFUNDED
    assert offer.status == OfferStatus.REFUNDED
