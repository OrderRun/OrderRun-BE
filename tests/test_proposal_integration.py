from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import inspect

from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus


def future_deadline(days: int = 1) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def proposal_payload(**overrides):
    payload = {
        "title": "강남역 커피 배달",
        "content": "스타벅스 아메리카노 아이스 2잔 부탁드립니다.",
        "deadline": future_deadline(),
        "errandFee": 5000,
    }
    payload.update(overrides)
    return payload


def test_list_public_requires_auth_and_supports_multi_status_filter(client, db, factory, auth_headers, sample_user):
    holding = factory.proposal(sample_user.id, ProposalStatus.HOLDING, "holding")
    posted = factory.proposal(sample_user.id, ProposalStatus.POSTED, "posted")
    offered = factory.proposal(sample_user.id, ProposalStatus.OFFERED, "offered")
    matched = factory.proposal(sample_user.id, ProposalStatus.MATCHED, "matched")
    cancelled = factory.proposal(sample_user.id, ProposalStatus.CANCELLED, "cancelled")

    unauthenticated = client.get("/v1/proposal")
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["error"]["code"] == "INVALID_TOKEN"

    response = client.get("/v1/proposal", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    ids = {item["id"] for item in body["data"]["content"]}
    assert ids == {holding.id, posted.id, offered.id, matched.id, cancelled.id}
    assert body["data"]["pageNumber"] == 0
    assert body["data"]["pageSize"] == 20
    assert body["data"]["totalElements"] == 5

    filtered = client.get("/v1/proposal?status=HOLDING&status=POSTED", headers=auth_headers)
    assert filtered.status_code == 200
    filtered_ids = {item["id"] for item in filtered.json()["data"]["content"]}
    assert filtered_ids == {holding.id, posted.id}

    invalid = client.get("/v1/proposal?status=INVALID", headers=auth_headers)
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"


def test_list_public_orders_by_deadline_then_creation_time(client, db, factory, auth_headers, sample_user):
    later = factory.proposal(sample_user.id, ProposalStatus.POSTED, "later")
    earlier = factory.proposal(sample_user.id, ProposalStatus.POSTED, "earlier")
    same_deadline_old = factory.proposal(sample_user.id, ProposalStatus.POSTED, "same-old")
    same_deadline_new = factory.proposal(sample_user.id, ProposalStatus.POSTED, "same-new")

    later.deadline = datetime.now(timezone.utc) + timedelta(days=3)
    later.meeting_at = later.deadline
    earlier.deadline = datetime.now(timezone.utc) + timedelta(days=1)
    earlier.meeting_at = earlier.deadline
    same_deadline = datetime.now(timezone.utc) + timedelta(days=2)
    same_deadline_old.deadline = same_deadline
    same_deadline_old.meeting_at = same_deadline
    same_deadline_new.deadline = same_deadline
    same_deadline_new.meeting_at = same_deadline
    db.commit()
    db.refresh(later)
    db.refresh(earlier)
    db.refresh(same_deadline_old)
    db.refresh(same_deadline_new)

    response = client.get("/v1/proposal", headers=auth_headers)

    assert response.status_code == 200
    ordered_ids = [item["id"] for item in response.json()["data"]["content"]]
    assert ordered_ids[:4] == [earlier.id, same_deadline_new.id, same_deadline_old.id, later.id]


def test_detail_returns_proposal_regardless_of_status(client, db, factory, auth_headers, sample_user):
    sample_user.level = 2
    db.commit()
    holding = factory.proposal(sample_user.id, ProposalStatus.HOLDING)
    cancelled = factory.proposal(sample_user.id, ProposalStatus.CANCELLED)

    holding_response = client.get(f"/v1/proposal/{holding.id}", headers=auth_headers)
    assert holding_response.status_code == 200
    holding_data = holding_response.json()["data"]
    assert holding_data["status"] == "HOLDING"
    assert holding_data["ordererId"] == sample_user.id
    assert holding_data["ordererName"] == sample_user.name
    assert holding_data["ordererLevel"] == 2
    assert holding_data["offers"] == []

    cancelled_response = client.get(f"/v1/proposal/{cancelled.id}", headers=auth_headers)
    assert cancelled_response.status_code == 200
    data = cancelled_response.json()["data"]
    assert data["status"] == "CANCELLED"
    assert data["matchedAt"] is None
    assert data["offers"] == []


def test_detail_returns_state_timestamps_when_matched(client, db, factory, auth_headers, sample_user):
    runner = factory.user("01099990003", name="Matched Runner")
    runner.level = 5
    db.commit()
    proposal = factory.proposal(sample_user.id, ProposalStatus.MATCHED)
    proposal.matched_at = datetime.now(timezone.utc)
    offer = Offer(proposal_id=proposal.id, runner_id=runner.id, status=OfferStatus.ACCEPTED)
    db.add(offer)
    db.commit()
    db.refresh(proposal)

    response = client.get(f"/v1/proposal/{proposal.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["matchedAt"] is not None
    assert data["ordererId"] == sample_user.id
    assert "missionId" not in data
    assert len(data["offers"]) == 1
    assert data["offers"][0]["id"] == offer.id
    assert data["offers"][0]["runnerName"] == "Matched Runner"
    assert data["offers"][0]["runnerLevel"] == 5


def test_list_own_returns_only_current_user_with_offers_and_multi_status_filter(client, db, factory, auth_headers, sample_user):
    other_user = factory.user(name="Old Offer Runner")
    own_posted = factory.proposal(sample_user.id, ProposalStatus.POSTED)
    own_holding = factory.proposal(sample_user.id, ProposalStatus.HOLDING)
    own_cancelled = factory.proposal(sample_user.id, ProposalStatus.CANCELLED)
    factory.proposal(other_user.id, ProposalStatus.POSTED)

    old_offer = Offer(
        proposal_id=own_posted.id,
        runner_id=other_user.id,
        status=OfferStatus.WAITING,
    )
    new_offer = Offer(
        proposal_id=own_posted.id,
        runner_id=factory.user("01099990001", name="New Offer Runner").id,
        status=OfferStatus.REJECTED,
    )
    db.add_all([old_offer, new_offer])
    db.commit()

    response = client.get("/v1/proposal/own?status=POSTED&status=CANCELLED", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()["data"]["content"]
    assert {item["id"] for item in items} == {own_posted.id, own_cancelled.id}
    posted_item = next(item for item in items if item["id"] == own_posted.id)
    assert posted_item["ordererId"] == sample_user.id
    assert posted_item["ordererName"] == sample_user.name
    assert posted_item["ordererLevel"] == sample_user.level
    assert posted_item["offerCount"] == 2
    assert [offer["id"] for offer in posted_item["offers"]] == [new_offer.id, old_offer.id]
    assert [offer["runnerName"] for offer in posted_item["offers"]] == ["New Offer Runner", "Old Offer Runner"]

    all_own_response = client.get("/v1/proposal/own", headers=auth_headers)
    assert {item["id"] for item in all_own_response.json()["data"]["content"]} == {
        own_posted.id,
        own_holding.id,
        own_cancelled.id,
    }


def test_list_own_orders_by_deadline_then_creation_time(client, db, factory, auth_headers, sample_user):
    later = factory.proposal(sample_user.id, ProposalStatus.POSTED, "later")
    earlier = factory.proposal(sample_user.id, ProposalStatus.POSTED, "earlier")
    same_deadline_old = factory.proposal(sample_user.id, ProposalStatus.POSTED, "same-old")
    same_deadline_new = factory.proposal(sample_user.id, ProposalStatus.POSTED, "same-new")

    later.deadline = datetime.now(timezone.utc) + timedelta(days=3)
    later.meeting_at = later.deadline
    earlier.deadline = datetime.now(timezone.utc) + timedelta(days=1)
    earlier.meeting_at = earlier.deadline
    same_deadline = datetime.now(timezone.utc) + timedelta(days=2)
    same_deadline_old.deadline = same_deadline
    same_deadline_old.meeting_at = same_deadline
    same_deadline_new.deadline = same_deadline
    same_deadline_new.meeting_at = same_deadline
    db.commit()
    db.refresh(later)
    db.refresh(earlier)
    db.refresh(same_deadline_old)
    db.refresh(same_deadline_new)

    response = client.get("/v1/proposal/own", headers=auth_headers)

    assert response.status_code == 200
    ordered_ids = [item["id"] for item in response.json()["data"]["content"]]
    assert ordered_ids[:4] == [earlier.id, same_deadline_new.id, same_deadline_old.id, later.id]


def test_create_proposal_validates_contract_and_stores_holding(client, db, factory, auth_headers, sample_user):
    response = client.post("/v1/proposal", json=proposal_payload(), headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "요청이 등록되었습니다."
    assert body["data"]["status"] == "HOLDING"
    assert set(body["data"]) == {"id", "title", "content", "deadline", "errandFee", "status"}

    proposal = db.query(Proposal).filter(Proposal.id == body["data"]["id"]).one()
    assert proposal.orderer_id == sample_user.id
    assert proposal.status == ProposalStatus.HOLDING


def test_create_proposal_validation_errors(client, auth_headers):
    cases = [
        (proposal_payload(title=" "), "VALIDATION_ERROR"),
        (proposal_payload(content=" "), "VALIDATION_ERROR"),
        (proposal_payload(title="가" * 51), "VALIDATION_ERROR"),
        (proposal_payload(content="가" * 501), "VALIDATION_ERROR"),
        (proposal_payload(deadline="not-a-datetime"), "INVALID_DATE_TIME_FORMAT"),
        (proposal_payload(deadline="2026-01-01T00:00:00"), "INVALID_DATE_TIME_FORMAT"),
        (
            proposal_payload(deadline=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat()),
            "PROPOSAL_DEADLINE_INVALID",
        ),
        (proposal_payload(errandFee=999), "PROPOSAL_ERRAND_FEE_INVALID"),
    ]

    for payload, expected_code in cases:
        response = client.post("/v1/proposal", json=payload, headers=auth_headers)
        assert response.status_code == 400
        assert response.json()["error"]["code"] == expected_code


def test_update_proposal_author_and_status_rules(client, db, factory, auth_headers, sample_user):
    other_user = factory.user()
    holding = factory.proposal(sample_user.id, ProposalStatus.HOLDING)
    posted = factory.proposal(sample_user.id, ProposalStatus.POSTED)
    offered = factory.proposal(sample_user.id, ProposalStatus.OFFERED)
    matched = factory.proposal(sample_user.id, ProposalStatus.MATCHED)
    cancelled = factory.proposal(sample_user.id, ProposalStatus.CANCELLED)

    forbidden = client.put(f"/v1/proposal/{holding.id}", json=proposal_payload(), headers=factory.headers_for(other_user))
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"

    for editable in [holding, posted]:
        response = client.put(
            f"/v1/proposal/{editable.id}",
            json=proposal_payload(title="수정된 제목"),
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["message"] == "제안이 수정되었습니다."
        assert response.json()["data"]["title"] == "수정된 제목"
        db.refresh(editable)
        assert editable.status == ProposalStatus.HOLDING
        assert editable.meeting_at == editable.deadline

    for not_editable in [offered, matched, cancelled]:
        response = client.put(f"/v1/proposal/{not_editable.id}", json=proposal_payload(), headers=auth_headers)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "PROPOSAL_NOT_EDITABLE"

    missing = client.put("/v1/proposal/999999", json=proposal_payload(), headers=auth_headers)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "PROPOSAL_NOT_FOUND"


def test_cancel_proposal_author_status_rules_and_rejects_waiting_offers(client, db, factory, auth_headers, sample_user):
    other_user = factory.user()
    holding = factory.proposal(sample_user.id, ProposalStatus.HOLDING)
    posted = factory.proposal(sample_user.id, ProposalStatus.POSTED)
    offered = factory.proposal(sample_user.id, ProposalStatus.OFFERED)
    matched = factory.proposal(sample_user.id, ProposalStatus.MATCHED)
    cancelled = factory.proposal(sample_user.id, ProposalStatus.CANCELLED)

    waiting_offer = Offer(
        proposal_id=offered.id,
        runner_id=other_user.id,
        status=OfferStatus.WAITING,
    )
    cancelled_offer = Offer(
        proposal_id=offered.id,
        runner_id=factory.user("01099990002").id,
        status=OfferStatus.REJECTED,
    )
    db.add_all([waiting_offer, cancelled_offer])
    db.commit()

    forbidden = client.post(f"/v1/proposal/{holding.id}/cancel", headers=factory.headers_for(other_user))
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"

    for cancellable in [holding, posted, offered]:
        response = client.post(f"/v1/proposal/{cancellable.id}/cancel", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "제안이 취소되었습니다."
        assert response.json()["data"]["status"] == "CANCELLED"

    db.refresh(waiting_offer)
    db.refresh(cancelled_offer)
    assert waiting_offer.status == OfferStatus.REJECTED
    assert cancelled_offer.status == OfferStatus.REJECTED
    for cancelled_proposal in [holding, posted, offered]:
        db.refresh(cancelled_proposal)
        assert cancelled_proposal.matched_at is None
        assert cancelled_proposal.delivery_reported_at is None
        assert cancelled_proposal.received_confirmed_at is None
        assert cancelled_proposal.disputed_at is None
        assert cancelled_proposal.refunded_at is None
        assert cancelled_proposal.settled_at is None
    assert waiting_offer.accepted_at is None
    assert waiting_offer.delivery_completed_at is None
    assert waiting_offer.receipt_confirmed_at is None
    assert waiting_offer.disputed_at is None
    assert waiting_offer.refunded_at is None
    assert waiting_offer.settled_at is None

    for not_cancellable in [matched, cancelled]:
        response = client.post(f"/v1/proposal/{not_cancellable.id}/cancel", headers=auth_headers)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "PROPOSAL_NOT_CANCELLABLE"


def test_confirm_received_marks_proposal_completed_without_finishing_offer(client, db, factory, auth_headers, sample_user):
    runner = factory.user("01055550001")
    proposal, offer = factory.execution(sample_user, runner, ProposalStatus.MATCHED, OfferStatus.ACCEPTED)

    response = client.post(f"/v1/proposal/{proposal.id}/confirm-received", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["message"] == "완료 확인되었습니다."
    assert response.json()["data"]["status"] == "ORDER_COMPLETED"
    assert response.json()["data"]["ordererId"] == sample_user.id
    assert response.json()["data"]["receivedConfirmedAt"] is not None
    db.refresh(proposal)
    db.refresh(offer)
    assert proposal.status == ProposalStatus.ORDER_COMPLETED
    assert offer.status == OfferStatus.ACCEPTED
    assert proposal.received_confirmed_at is not None
    assert offer.receipt_confirmed_at is not None
    assert proposal.delivery_reported_at is None
    assert offer.delivery_completed_at is None
    assert proposal.disputed_at is None
    assert offer.disputed_at is None
    assert proposal.refunded_at is None
    assert offer.refunded_at is None
    assert proposal.settled_at is None
    assert offer.settled_at is None


def test_confirm_received_after_runner_completion_marks_both_all_completed(client, db, factory, auth_headers, sample_user):
    runner = factory.user("01055550002")
    sample_user.level = 6
    proposal, offer = factory.execution(sample_user, runner, ProposalStatus.MATCHED, OfferStatus.RUNNER_COMPLETED)
    proposal.delivery_reported_at = datetime.now(timezone.utc)
    offer.delivery_completed_at = proposal.delivery_reported_at
    db.commit()

    response = client.post(f"/v1/proposal/{proposal.id}/confirm-received", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ALL_COMPLETED"
    assert response.json()["data"]["ordererLevel"] == 6
    assert response.json()["data"]["offers"][0]["runnerLevel"] == 1
    db.refresh(proposal)
    db.refresh(offer)
    db.refresh(runner)
    db.refresh(sample_user)
    assert proposal.status == ProposalStatus.ALL_COMPLETED
    assert offer.status == OfferStatus.ALL_COMPLETED
    assert runner.level == 1
    assert sample_user.level == 6
    assert proposal.delivery_reported_at is not None
    assert offer.delivery_completed_at is not None
    assert proposal.received_confirmed_at is not None
    assert offer.receipt_confirmed_at is not None
    assert proposal.disputed_at is None
    assert offer.disputed_at is None
    assert proposal.refunded_at is None
    assert offer.refunded_at is None
    assert proposal.settled_at is None
    assert offer.settled_at is None


def test_raise_proposal_dispute_updates_both_statuses_and_timestamps(client, db, factory, auth_headers, sample_user):
    runner = factory.user("01055550003")
    proposal, offer = factory.execution(sample_user, runner, ProposalStatus.MATCHED, OfferStatus.ACCEPTED)
    offer.accepted_at = datetime.now(timezone.utc)
    proposal.matched_at = offer.accepted_at
    db.commit()

    response = client.post(
        f"/v1/proposal/{proposal.id}/dispute",
        json={"disputeReason": "물품 상태 불량"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "DISPUTED"
    assert data["disputedAt"] is not None
    db.refresh(proposal)
    db.refresh(offer)
    assert proposal.status == ProposalStatus.DISPUTED
    assert offer.status == OfferStatus.DISPUTED
    assert proposal.disputed_at is not None
    assert offer.disputed_at is not None
    assert proposal.refunded_at is None
    assert offer.refunded_at is None
    assert proposal.settled_at is None
    assert offer.settled_at is None


def test_proposal_model_contract(db):
    table = inspect(db.bind).get_columns("proposals")
    columns = {column["name"]: column for column in table}
    assert columns["orderer_id"]["nullable"] is False
    assert columns["title"]["nullable"] is False
    assert columns["content"]["nullable"] is False
    assert columns["deadline"]["nullable"] is False
    assert columns["errand_fee"]["nullable"] is False
    assert columns["meeting_at"]["nullable"] is False
    assert columns["item_price"]["nullable"] is False
    assert columns["deposit"]["nullable"] is False
    assert {status.value for status in ProposalStatus} == {
        "HOLDING",
        "POSTED",
        "OFFERED",
        "MATCHED",
        "ORDER_COMPLETED",
        "ALL_COMPLETED",
        "DISPUTED",
        "REFUNDED",
        "CANCELLED",
    }
    foreign_keys = inspect(db.bind).get_foreign_keys("proposals")
    assert foreign_keys == []
