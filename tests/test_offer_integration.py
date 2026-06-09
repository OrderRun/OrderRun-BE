from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus


def offer_payload(proposal_id: int, **overrides) -> dict:
    payload = {"proposalId": proposal_id}
    payload.update(overrides)
    return payload


def test_create_offer_with_proposal_id_only_and_marks_proposal_offered(client, db, factory, sample_user):
    runner = factory.user("01077770001", name="Runner One")
    proposal = factory.proposal(sample_user.id, ProposalStatus.POSTED)

    response = client.post(
        "/v1/offer",
        json=offer_payload(proposal.id),
        headers=factory.headers_for(runner),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "제안이 제출되었습니다."
    assert body["data"] == {
        "id": body["data"]["id"],
        "proposalId": proposal.id,
        "runnerId": runner.id,
        "runnerName": "Runner One",
        "status": "WAITING",
        "acceptedAt": None,
        "deliveryCompletedAt": None,
        "receiptConfirmedAt": None,
        "disputedAt": None,
        "refundedAt": None,
        "createdAt": body["data"]["createdAt"],
    }

    db.refresh(proposal)
    offer = db.query(Offer).filter(Offer.id == body["data"]["id"]).one()
    assert offer.status == OfferStatus.WAITING
    assert proposal.status == ProposalStatus.OFFERED


def test_create_second_offer_keeps_proposal_offered(client, db, factory, sample_user):
    runner1 = factory.user("01077770002")
    runner2 = factory.user("01077770003")
    proposal = factory.proposal(sample_user.id, ProposalStatus.OFFERED)

    first = client.post("/v1/offer", json=offer_payload(proposal.id), headers=factory.headers_for(runner1))
    second = client.post("/v1/offer", json=offer_payload(proposal.id), headers=factory.headers_for(runner2))

    assert first.status_code == 201
    assert second.status_code == 201
    db.refresh(proposal)
    assert proposal.status == ProposalStatus.OFFERED


def test_get_offers_returns_latest_first_and_supports_multi_status_filter(client, db, factory, sample_user):
    runner1 = factory.user("01077770004", name="Old Runner")
    runner2 = factory.user("01077770005", name="New Runner")
    runner3 = factory.user("01077770019", name="Accepted Runner")
    other_orderer = factory.user("01077770006")
    proposal = factory.proposal(sample_user.id, ProposalStatus.OFFERED)
    other_proposal = factory.proposal(sample_user.id, ProposalStatus.OFFERED)

    old_offer = Offer(proposal_id=proposal.id, runner_id=runner1.id, status=OfferStatus.WAITING)
    new_offer = Offer(proposal_id=proposal.id, runner_id=runner2.id, status=OfferStatus.REJECTED)
    accepted_offer = Offer(proposal_id=proposal.id, runner_id=runner3.id, status=OfferStatus.ACCEPTED)
    other_offer = Offer(proposal_id=other_proposal.id, runner_id=runner1.id)
    db.add_all([old_offer, new_offer, accepted_offer, other_offer])
    db.commit()

    response = client.get(f"/v1/offer?proposalId={proposal.id}", headers=factory.headers_for(other_orderer))
    assert response.status_code == 200
    items = response.json()["data"]
    assert [item["id"] for item in items] == [accepted_offer.id, new_offer.id, old_offer.id]
    assert [item["runnerName"] for item in items] == ["Accepted Runner", "New Runner", "Old Runner"]

    filtered = client.get(
        f"/v1/offer?proposalId={proposal.id}&status=WAITING&status=ACCEPTED",
        headers=factory.headers_for(other_orderer),
    )
    assert filtered.status_code == 200
    filtered_items = filtered.json()["data"]
    assert [item["id"] for item in filtered_items] == [accepted_offer.id, old_offer.id]

    invalid = client.get(f"/v1/offer?proposalId={proposal.id}&status=INVALID", headers=factory.headers_for(other_orderer))
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"


def test_get_offer_detail_allows_any_logged_in_user(client, db, factory, sample_user):
    runner = factory.user("01077770007")
    stranger = factory.user("01077770008")
    proposal = factory.proposal(sample_user.id, ProposalStatus.OFFERED)
    offer = Offer(proposal_id=proposal.id, runner_id=runner.id)
    db.add(offer)
    db.commit()

    runner_response = client.get(f"/v1/offer/{offer.id}", headers=factory.headers_for(runner))
    orderer_response = client.get(f"/v1/offer/{offer.id}", headers=factory.headers_for(sample_user))
    stranger_response = client.get(f"/v1/offer/{offer.id}", headers=factory.headers_for(stranger))

    assert runner_response.status_code == 200
    assert orderer_response.status_code == 200
    assert stranger_response.status_code == 200
    assert "missionId" not in runner_response.json()["data"]
    assert runner_response.json()["data"]["acceptedAt"] is None


def test_get_offer_detail_returns_state_timestamps_when_accepted(client, db, factory, sample_user):
    runner = factory.user("01077770020")
    proposal = factory.proposal(sample_user.id, ProposalStatus.MATCHED)
    offer = Offer(proposal_id=proposal.id, runner_id=runner.id, status=OfferStatus.ACCEPTED)
    offer.accepted_at = datetime.now(timezone.utc)
    db.add(offer)
    db.commit()
    db.refresh(offer)

    response = client.get(f"/v1/offer/{offer.id}", headers=factory.headers_for(runner))

    assert response.status_code == 200
    assert response.json()["data"]["acceptedAt"] is not None
    assert "missionId" not in response.json()["data"]


def test_get_own_offers_supports_paging_and_multi_status_filter(client, db, factory, sample_user):
    runner = factory.user("01077770009")
    other_runner = factory.user("01077770010")
    proposal1 = factory.proposal(sample_user.id, ProposalStatus.OFFERED)
    proposal2 = factory.proposal(sample_user.id, ProposalStatus.OFFERED)
    proposal3 = factory.proposal(sample_user.id, ProposalStatus.OFFERED)
    waiting = Offer(proposal_id=proposal1.id, runner_id=runner.id, status=OfferStatus.WAITING)
    accepted = Offer(proposal_id=proposal2.id, runner_id=runner.id, status=OfferStatus.ACCEPTED)
    other = Offer(proposal_id=proposal3.id, runner_id=other_runner.id, status=OfferStatus.WAITING)
    db.add_all([waiting, accepted, other])
    db.commit()

    response = client.get("/v1/offer/own?status=WAITING&status=ACCEPTED&page=0&size=10", headers=factory.headers_for(runner))

    assert response.status_code == 200
    page = response.json()["data"]
    assert page["totalElements"] == 2
    assert [item["id"] for item in page["content"]] == [accepted.id, waiting.id]


def test_accept_offer_updates_states_and_timestamps(client, db, factory, sample_user):
    runner1 = factory.user("01077770011")
    runner2 = factory.user("01077770012")
    proposal = factory.proposal(sample_user.id, ProposalStatus.OFFERED)
    selected = Offer(proposal_id=proposal.id, runner_id=runner1.id)
    other = Offer(proposal_id=proposal.id, runner_id=runner2.id)
    db.add_all([selected, other])
    db.commit()

    response = client.post(
        f"/v1/offer/{selected.id}/accept",
        headers=factory.headers_for(sample_user),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "제안이 수락되었습니다."
    assert body["data"]["proposalId"] == proposal.id
    assert body["data"]["offerId"] == selected.id
    assert body["data"]["proposalStatus"] == "MATCHED"
    assert body["data"]["acceptedOfferStatus"] == "ACCEPTED"
    assert body["data"]["rejectedOfferCount"] == 1
    assert "missionStatus" not in body["data"]
    assert "missionId" not in body["data"]
    assert body["data"]["acceptedAt"] is not None
    assert "runFee" not in body["data"]
    assert "itemPrice" not in body["data"]
    assert "totalAmount" not in body["data"]

    db.refresh(proposal)
    db.refresh(selected)
    db.refresh(other)
    assert proposal.status == ProposalStatus.MATCHED
    assert selected.status == OfferStatus.ACCEPTED
    assert other.status == OfferStatus.REJECTED
    assert proposal.matched_at is not None
    assert selected.accepted_at is not None


def test_accept_offer_domain_and_validation_errors(client, db, factory, sample_user):
    runner = factory.user("01077770013")
    other_user = factory.user("01077770014")
    proposal = factory.proposal(sample_user.id, ProposalStatus.OFFERED)
    posted_proposal = factory.proposal(sample_user.id, ProposalStatus.POSTED)
    accepted_offer = Offer(proposal_id=proposal.id, runner_id=runner.id, status=OfferStatus.ACCEPTED)
    posted_offer = Offer(proposal_id=posted_proposal.id, runner_id=runner.id, status=OfferStatus.WAITING)
    db.add_all([accepted_offer, posted_offer])
    db.commit()

    forbidden = client.post(
        f"/v1/offer/{posted_offer.id}/accept",
        headers=factory.headers_for(other_user),
    )
    runner_forbidden = client.post(
        f"/v1/offer/{posted_offer.id}/accept",
        headers=factory.headers_for(runner),
    )
    not_acceptable = client.post(
        f"/v1/offer/{accepted_offer.id}/accept",
        headers=factory.headers_for(sample_user),
    )
    not_matchable = client.post(
        f"/v1/offer/{posted_offer.id}/accept",
        headers=factory.headers_for(sample_user),
    )

    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"
    assert runner_forbidden.status_code == 403
    assert runner_forbidden.json()["error"]["code"] == "FORBIDDEN"
    assert not_acceptable.status_code == 409
    assert not_acceptable.json()["error"]["code"] == "OFFER_NOT_ACCEPTABLE"
    assert not_matchable.status_code == 409
    assert not_matchable.json()["error"]["code"] == "PROPOSAL_NOT_MATCHABLE"


def test_existing_active_offer_blocks_accept(client, db, factory, sample_user):
    runner = factory.user("01077770015")
    other_runner = factory.user("01077770021")
    proposal = factory.proposal(sample_user.id, ProposalStatus.OFFERED)
    offer = Offer(proposal_id=proposal.id, runner_id=runner.id)
    active_offer = Offer(proposal_id=proposal.id, runner_id=other_runner.id, status=OfferStatus.ACCEPTED)
    db.add_all([offer, active_offer])
    db.commit()

    response = client.post(
        f"/v1/offer/{offer.id}/accept",
        headers=factory.headers_for(sample_user),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PROPOSAL_NOT_MATCHABLE"


def test_cancel_offer_author_and_status_rules(client, db, factory, sample_user):
    runner = factory.user("01077770016")
    other_runner = factory.user("01077770017")
    proposal = factory.proposal(sample_user.id, ProposalStatus.OFFERED)
    waiting = Offer(proposal_id=proposal.id, runner_id=runner.id, status=OfferStatus.WAITING)
    accepted = Offer(proposal_id=proposal.id, runner_id=other_runner.id, status=OfferStatus.ACCEPTED)
    db.add_all([waiting, accepted])
    db.commit()

    forbidden = client.delete(f"/v1/offer/{waiting.id}", headers=factory.headers_for(other_runner))
    not_cancellable = client.delete(f"/v1/offer/{accepted.id}", headers=factory.headers_for(other_runner))
    cancelled = client.delete(f"/v1/offer/{waiting.id}", headers=factory.headers_for(runner))

    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"
    assert not_cancellable.status_code == 409
    assert not_cancellable.json()["error"]["code"] == "OFFER_NOT_CANCELLABLE"
    assert cancelled.status_code == 204
    assert cancelled.content == b""

    db.refresh(waiting)
    assert waiting.status == OfferStatus.CANCELLED


def test_complete_delivery_marks_offer_completed_without_finishing_proposal(client, db, factory, sample_user):
    runner = factory.user("01077770022")
    proposal = factory.proposal(sample_user.id, ProposalStatus.MATCHED)
    offer = Offer(proposal_id=proposal.id, runner_id=runner.id, status=OfferStatus.ACCEPTED)
    offer.accepted_at = datetime.now(timezone.utc)
    db.add(offer)
    db.commit()

    response = client.post(
        f"/v1/offer/{offer.id}/complete-delivery",
        json={"proofImageUrl": "https://example.com/proof.jpg"},
        headers=factory.headers_for(runner),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "RUNNER_COMPLETED"
    assert data["deliveryCompletedAt"] is not None

    db.refresh(offer)
    db.refresh(proposal)
    assert offer.status == OfferStatus.RUNNER_COMPLETED
    assert offer.delivery_completed_at is not None
    assert proposal.status == ProposalStatus.MATCHED
    assert proposal.delivery_reported_at is not None


def test_complete_delivery_after_orderer_completion_marks_both_all_completed(client, db, factory, sample_user):
    runner = factory.user("01077770025")
    proposal = factory.proposal(sample_user.id, ProposalStatus.ORDER_COMPLETED)
    offer = Offer(proposal_id=proposal.id, runner_id=runner.id, status=OfferStatus.ACCEPTED)
    offer.accepted_at = datetime.now(timezone.utc)
    db.add(offer)
    db.commit()

    response = client.post(
        f"/v1/offer/{offer.id}/complete-delivery",
        json={"proofImageUrl": "https://example.com/proof.jpg"},
        headers=factory.headers_for(runner),
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ALL_COMPLETED"
    db.refresh(offer)
    db.refresh(proposal)
    assert offer.status == OfferStatus.ALL_COMPLETED
    assert proposal.status == ProposalStatus.ALL_COMPLETED


def test_complete_delivery_forbidden_and_wrong_status_errors(client, db, factory, sample_user):
    runner = factory.user("01077770023")
    other_runner = factory.user("01077770024")
    proposal = factory.proposal(sample_user.id, ProposalStatus.MATCHED)
    accepted_offer = Offer(proposal_id=proposal.id, runner_id=runner.id, status=OfferStatus.ACCEPTED)
    accepted_offer.accepted_at = datetime.now(timezone.utc)
    waiting_proposal = factory.proposal(sample_user.id, ProposalStatus.OFFERED)
    waiting_offer = Offer(proposal_id=waiting_proposal.id, runner_id=runner.id, status=OfferStatus.WAITING)
    db.add_all([accepted_offer, waiting_offer])
    db.commit()

    forbidden = client.post(
        f"/v1/offer/{accepted_offer.id}/complete-delivery",
        json={"proofImageUrl": None},
        headers=factory.headers_for(other_runner),
    )
    not_updatable = client.post(
        f"/v1/offer/{waiting_offer.id}/complete-delivery",
        json={"proofImageUrl": None},
        headers=factory.headers_for(runner),
    )

    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"
    assert not_updatable.status_code == 409
    assert not_updatable.json()["error"]["code"] == "OFFER_NOT_UPDATABLE"


def test_offer_validation_and_domain_errors(client, db, factory, sample_user):
    runner = factory.user("01077770018")
    proposal = factory.proposal(sample_user.id, ProposalStatus.POSTED)
    closed_proposal = factory.proposal(sample_user.id, ProposalStatus.MATCHED)

    invalid = client.post("/v1/offer", json={"proposalId": 0}, headers=factory.headers_for(runner))
    missing = client.post("/v1/offer", json=offer_payload(999999), headers=factory.headers_for(runner))
    closed = client.post("/v1/offer", json=offer_payload(closed_proposal.id), headers=factory.headers_for(runner))
    first = client.post("/v1/offer", json=offer_payload(proposal.id), headers=factory.headers_for(runner))
    duplicate = client.post("/v1/offer", json=offer_payload(proposal.id), headers=factory.headers_for(runner))
    self_offer = client.post("/v1/offer", json=offer_payload(proposal.id), headers=factory.headers_for(sample_user))

    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "PROPOSAL_NOT_FOUND"
    assert closed.status_code == 409
    assert closed.json()["error"]["code"] == "PROPOSAL_NOT_OPEN"
    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE_OFFER"
    assert self_offer.status_code == 400
    assert self_offer.json()["error"]["code"] == "SELF_OFFER_NOT_ALLOWED"
