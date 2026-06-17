from __future__ import annotations

from datetime import datetime, timezone

from app.models.offer import OfferStatus
from app.models.proposal import ProposalStatus


def test_confirm_payment_posts_holding_proposal_without_request_body(client, db, factory, sample_user):
    proposal = factory.proposal(sample_user.id, ProposalStatus.HOLDING)

    response = client.post(f"/v1/admin/proposal/{proposal.id}/confirm-payment")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "POSTED"
    db.refresh(proposal)
    assert proposal.status == ProposalStatus.POSTED


def test_confirm_payment_rejects_non_holding_proposal(client, db, factory, sample_user):
    proposal = factory.proposal(sample_user.id, ProposalStatus.POSTED)

    response = client.post(f"/v1/admin/proposal/{proposal.id}/confirm-payment")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_STATUS"


def test_list_pending_payment_proposals_without_auth(client, factory, sample_user):
    holding = factory.proposal(sample_user.id, ProposalStatus.HOLDING)
    factory.proposal(sample_user.id, ProposalStatus.POSTED)

    response = client.get("/v1/admin/proposal/pending-payment")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [holding.id]


def test_resolve_offer_sets_resolved_from_disputed(client, db, factory, sample_user):
    runner = factory.user("01066660003")
    proposal, offer = factory.execution(sample_user, runner, ProposalStatus.DISPUTED, OfferStatus.DISPUTED)
    disputed_at = datetime.now(timezone.utc)
    proposal.disputed_at = disputed_at
    offer.disputed_at = disputed_at
    db.commit()

    response = client.post(f"/v1/admin/offer/{offer.id}/resolve")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "RESOLVED"
    assert response.json()["data"]["resolvedAt"] is not None
    db.refresh(proposal)
    db.refresh(offer)
    assert proposal.status == ProposalStatus.RESOLVED
    assert offer.status == OfferStatus.RESOLVED
    assert proposal.resolved_at is not None
    assert offer.resolved_at is not None
    assert proposal.disputed_at is not None
    assert offer.disputed_at is not None
    assert proposal.settled_at is None
    assert offer.settled_at is None
