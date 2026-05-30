from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.security import create_access_token
from app.models.mission import Mission, MissionStatus
from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.user import User


def headers_for(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': user.id})}"}


def make_user(db, phone: str, name: str = "Offer User") -> User:
    user = User(name=name, phone=phone, alarm_enabled=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_proposal(db, orderer_id: str, proposal_status: ProposalStatus = ProposalStatus.POSTED) -> Proposal:
    deadline = datetime.now(timezone.utc) + timedelta(days=1)
    proposal = Proposal(
        orderer_id=orderer_id,
        title="요청",
        content="요청 내용",
        deadline=deadline,
        errand_fee=5000,
        status=proposal_status,
        meeting_at=deadline,
        item_price=0,
        deposit=0,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


def offer_payload(proposal_id: int, **overrides) -> dict:
    payload = {"proposalId": proposal_id}
    payload.update(overrides)
    return payload


def test_create_offer_with_proposal_id_only_and_marks_proposal_offered(client, db, sample_user):
    runner = make_user(db, "01077770001", name="Runner One")
    proposal = make_proposal(db, sample_user.id, ProposalStatus.POSTED)

    response = client.post(
        "/v1/offer",
        json=offer_payload(proposal.id),
        headers=headers_for(runner),
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
        "createdAt": body["data"]["createdAt"],
    }

    db.refresh(proposal)
    offer = db.query(Offer).filter(Offer.id == body["data"]["id"]).one()
    assert offer.status == OfferStatus.WAITING
    assert proposal.status == ProposalStatus.OFFERED


def test_create_second_offer_keeps_proposal_offered(client, db, sample_user):
    runner1 = make_user(db, "01077770002")
    runner2 = make_user(db, "01077770003")
    proposal = make_proposal(db, sample_user.id, ProposalStatus.OFFERED)

    first = client.post("/v1/offer", json=offer_payload(proposal.id), headers=headers_for(runner1))
    second = client.post("/v1/offer", json=offer_payload(proposal.id), headers=headers_for(runner2))

    assert first.status_code == 201
    assert second.status_code == 201
    db.refresh(proposal)
    assert proposal.status == ProposalStatus.OFFERED


def test_get_offers_returns_latest_first_for_authenticated_user(client, db, sample_user):
    runner1 = make_user(db, "01077770004", name="Old Runner")
    runner2 = make_user(db, "01077770005", name="New Runner")
    other_orderer = make_user(db, "01077770006")
    proposal = make_proposal(db, sample_user.id, ProposalStatus.OFFERED)
    other_proposal = make_proposal(db, sample_user.id, ProposalStatus.OFFERED)

    old_offer = Offer(proposal_id=proposal.id, runner_id=runner1.id)
    new_offer = Offer(proposal_id=proposal.id, runner_id=runner2.id)
    other_offer = Offer(proposal_id=other_proposal.id, runner_id=runner1.id)
    db.add_all([old_offer, new_offer, other_offer])
    db.commit()

    response = client.get(f"/v1/offer?proposalId={proposal.id}", headers=headers_for(other_orderer))
    assert response.status_code == 200
    items = response.json()["data"]
    assert [item["id"] for item in items] == [new_offer.id, old_offer.id]
    assert [item["runnerName"] for item in items] == ["New Runner", "Old Runner"]


def test_get_offer_detail_allows_runner_and_orderer_only(client, db, sample_user):
    runner = make_user(db, "01077770007")
    stranger = make_user(db, "01077770008")
    proposal = make_proposal(db, sample_user.id, ProposalStatus.OFFERED)
    offer = Offer(proposal_id=proposal.id, runner_id=runner.id)
    db.add(offer)
    db.commit()

    runner_response = client.get(f"/v1/offer/{offer.id}", headers=headers_for(runner))
    orderer_response = client.get(f"/v1/offer/{offer.id}", headers=headers_for(sample_user))
    forbidden = client.get(f"/v1/offer/{offer.id}", headers=headers_for(stranger))

    assert runner_response.status_code == 200
    assert orderer_response.status_code == 200
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"


def test_get_own_offers_supports_paging_and_status_filter(client, db, sample_user):
    runner = make_user(db, "01077770009")
    other_runner = make_user(db, "01077770010")
    proposal1 = make_proposal(db, sample_user.id, ProposalStatus.OFFERED)
    proposal2 = make_proposal(db, sample_user.id, ProposalStatus.OFFERED)
    proposal3 = make_proposal(db, sample_user.id, ProposalStatus.OFFERED)
    waiting = Offer(proposal_id=proposal1.id, runner_id=runner.id, status=OfferStatus.WAITING)
    accepted = Offer(proposal_id=proposal2.id, runner_id=runner.id, status=OfferStatus.ACCEPTED)
    other = Offer(proposal_id=proposal3.id, runner_id=other_runner.id, status=OfferStatus.WAITING)
    db.add_all([waiting, accepted, other])
    db.commit()

    response = client.get("/v1/offer/own?status=WAITING&page=1&size=10", headers=headers_for(runner))

    assert response.status_code == 200
    page = response.json()["data"]
    assert page["total"] == 1
    assert [item["id"] for item in page["items"]] == [waiting.id]


def test_accept_offer_creates_mission_and_updates_states(client, db, sample_user):
    runner1 = make_user(db, "01077770011")
    runner2 = make_user(db, "01077770012")
    proposal = make_proposal(db, sample_user.id, ProposalStatus.OFFERED)
    selected = Offer(proposal_id=proposal.id, runner_id=runner1.id)
    other = Offer(proposal_id=proposal.id, runner_id=runner2.id)
    db.add_all([selected, other])
    db.commit()

    response = client.post(
        f"/v1/offer/{selected.id}/accept",
        json={"runFee": 3000, "itemPrice": 2000},
        headers=headers_for(sample_user),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "제안이 수락되었습니다."
    assert body["data"]["proposalId"] == proposal.id
    assert body["data"]["offerId"] == selected.id
    assert body["data"]["proposalStatus"] == "MATCHED"
    assert body["data"]["acceptedOfferStatus"] == "ACCEPTED"
    assert body["data"]["rejectedOfferCount"] == 1
    assert body["data"]["missionStatus"] == "CREATED"
    assert body["data"]["runFee"] == 3000
    assert body["data"]["itemPrice"] == 2000
    assert body["data"]["totalAmount"] == 5000

    db.refresh(proposal)
    db.refresh(selected)
    db.refresh(other)
    mission = db.query(Mission).filter(Mission.id == body["data"]["missionId"]).one()
    assert proposal.status == ProposalStatus.MATCHED
    assert selected.status == OfferStatus.ACCEPTED
    assert other.status == OfferStatus.REJECTED
    assert mission.status == MissionStatus.CREATED
    assert mission.contract_amount == 5000
    assert mission.total_amount == 5000


def test_accept_offer_domain_and_validation_errors(client, db, sample_user):
    runner = make_user(db, "01077770013")
    other_user = make_user(db, "01077770014")
    proposal = make_proposal(db, sample_user.id, ProposalStatus.OFFERED)
    posted_proposal = make_proposal(db, sample_user.id, ProposalStatus.POSTED)
    accepted_offer = Offer(proposal_id=proposal.id, runner_id=runner.id, status=OfferStatus.ACCEPTED)
    posted_offer = Offer(proposal_id=posted_proposal.id, runner_id=runner.id, status=OfferStatus.WAITING)
    db.add_all([accepted_offer, posted_offer])
    db.commit()

    missing_body = client.post(f"/v1/offer/{posted_offer.id}/accept", json={}, headers=headers_for(sample_user))
    forbidden = client.post(
        f"/v1/offer/{posted_offer.id}/accept",
        json={"runFee": 1, "itemPrice": 1},
        headers=headers_for(other_user),
    )
    not_acceptable = client.post(
        f"/v1/offer/{accepted_offer.id}/accept",
        json={"runFee": 1, "itemPrice": 1},
        headers=headers_for(sample_user),
    )
    not_matchable = client.post(
        f"/v1/offer/{posted_offer.id}/accept",
        json={"runFee": 1, "itemPrice": 1},
        headers=headers_for(sample_user),
    )

    assert missing_body.status_code == 400
    assert missing_body.json()["error"]["code"] == "VALIDATION_ERROR"
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"
    assert not_acceptable.status_code == 409
    assert not_acceptable.json()["error"]["code"] == "OFFER_NOT_ACCEPTABLE"
    assert not_matchable.status_code == 409
    assert not_matchable.json()["error"]["code"] == "PROPOSAL_NOT_MATCHABLE"


def test_duplicate_mission_blocks_accept(client, db, sample_user):
    runner = make_user(db, "01077770015")
    proposal = make_proposal(db, sample_user.id, ProposalStatus.OFFERED)
    offer = Offer(proposal_id=proposal.id, runner_id=runner.id)
    db.add(offer)
    db.commit()
    mission = Mission(
        proposal_id=proposal.id,
        offer_id=offer.id,
        orderer_id=sample_user.id,
        runner_id=runner.id,
        contract_amount=100,
        run_fee=50,
        item_price=50,
        total_amount=100,
        status=MissionStatus.CREATED,
    )
    db.add(mission)
    db.commit()

    response = client.post(
        f"/v1/offer/{offer.id}/accept",
        json={"runFee": 1, "itemPrice": 1},
        headers=headers_for(sample_user),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "MISSION_ALREADY_EXISTS"


def test_cancel_offer_author_and_status_rules(client, db, sample_user):
    runner = make_user(db, "01077770016")
    other_runner = make_user(db, "01077770017")
    proposal = make_proposal(db, sample_user.id, ProposalStatus.OFFERED)
    waiting = Offer(proposal_id=proposal.id, runner_id=runner.id, status=OfferStatus.WAITING)
    accepted = Offer(proposal_id=proposal.id, runner_id=other_runner.id, status=OfferStatus.ACCEPTED)
    db.add_all([waiting, accepted])
    db.commit()

    forbidden = client.delete(f"/v1/offer/{waiting.id}", headers=headers_for(other_runner))
    not_cancellable = client.delete(f"/v1/offer/{accepted.id}", headers=headers_for(other_runner))
    cancelled = client.delete(f"/v1/offer/{waiting.id}", headers=headers_for(runner))

    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"
    assert not_cancellable.status_code == 409
    assert not_cancellable.json()["error"]["code"] == "OFFER_NOT_CANCELLABLE"
    assert cancelled.status_code == 204
    assert cancelled.content == b""

    db.refresh(waiting)
    assert waiting.status == OfferStatus.CANCELLED


def test_offer_validation_and_domain_errors(client, db, sample_user):
    runner = make_user(db, "01077770018")
    proposal = make_proposal(db, sample_user.id, ProposalStatus.POSTED)
    closed_proposal = make_proposal(db, sample_user.id, ProposalStatus.MATCHED)

    invalid = client.post("/v1/offer", json={"proposalId": 0}, headers=headers_for(runner))
    missing = client.post("/v1/offer", json=offer_payload(999999), headers=headers_for(runner))
    closed = client.post("/v1/offer", json=offer_payload(closed_proposal.id), headers=headers_for(runner))
    first = client.post("/v1/offer", json=offer_payload(proposal.id), headers=headers_for(runner))
    duplicate = client.post("/v1/offer", json=offer_payload(proposal.id), headers=headers_for(runner))
    self_offer = client.post("/v1/offer", json=offer_payload(proposal.id), headers=headers_for(sample_user))

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
