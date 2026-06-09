from __future__ import annotations

from app.models.offer import OfferStatus
from app.models.proposal import ProposalStatus


def test_confirm_payment_posts_holding_proposal_without_request_body(client, db, factory, auth_headers, sample_user):
    proposal = factory.proposal(sample_user.id, ProposalStatus.HOLDING)

    response = client.post(f"/api/v1/admin/proposal/{proposal.id}/confirm-payment", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "POSTED"
    db.refresh(proposal)
    assert proposal.status == ProposalStatus.POSTED


def test_confirm_payment_rejects_non_holding_proposal(client, db, factory, auth_headers, sample_user):
    proposal = factory.proposal(sample_user.id, ProposalStatus.POSTED)

    response = client.post(f"/api/v1/admin/proposal/{proposal.id}/confirm-payment", headers=auth_headers)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_STATUS"


def test_confirm_offer_settlement_sets_settled(client, db, factory, auth_headers, sample_user):
    runner = factory.user("01066660001")
    proposal, offer = factory.execution(
        sample_user,
        runner,
        ProposalStatus.ALL_COMPLETED,
        OfferStatus.ALL_COMPLETED,
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


def test_confirm_offer_settlement_rejects_non_completed(client, factory, auth_headers, sample_user):
    runner = factory.user("01066660002")
    _, offer = factory.execution(sample_user, runner, ProposalStatus.COMPLETED, OfferStatus.COMPLETED)

    response = client.post(f"/api/v1/admin/offer/{offer.id}/confirm-settlement", headers=auth_headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "OFFER_NOT_UPDATABLE"


def test_refund_offer_sets_refunded_from_disputed(client, db, factory, auth_headers, sample_user):
    runner = factory.user("01066660003")
    proposal, offer = factory.execution(sample_user, runner, ProposalStatus.DISPUTED, OfferStatus.DISPUTED)

    response = client.post(f"/api/v1/admin/offer/{offer.id}/refund", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "REFUNDED"
    assert response.json()["data"]["refundedAt"] is not None
    db.refresh(proposal)
    db.refresh(offer)
    assert proposal.status == ProposalStatus.REFUNDED
    assert offer.status == OfferStatus.REFUNDED
