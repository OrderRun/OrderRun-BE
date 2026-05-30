from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import inspect

from app.core.security import create_access_token
from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.user import User


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


def make_user(db, phone: str = "01099990000") -> User:
    user = User(name="Other User", phone=phone, alarm_enabled=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def headers_for(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': user.id})}"}


def make_proposal(db, orderer_id: str, status: ProposalStatus, title: str = "요청") -> Proposal:
    deadline = datetime.now(timezone.utc) + timedelta(days=1)
    proposal = Proposal(
        orderer_id=orderer_id,
        title=title,
        content="요청 내용",
        deadline=deadline,
        errand_fee=5000,
        status=status,
        meeting_at=deadline,
        item_price=0,
        deposit=0,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


def test_list_public_requires_auth_and_exposes_only_posted_or_offered(client, db, auth_headers, sample_user):
    posted = make_proposal(db, sample_user.id, ProposalStatus.POSTED, "posted")
    offered = make_proposal(db, sample_user.id, ProposalStatus.OFFERED, "offered")
    make_proposal(db, sample_user.id, ProposalStatus.HOLDING, "holding")
    make_proposal(db, sample_user.id, ProposalStatus.MATCHED, "matched")
    make_proposal(db, sample_user.id, ProposalStatus.CANCELLED, "cancelled")

    unauthenticated = client.get("/v1/proposal")
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["error"]["code"] == "INVALID_TOKEN"

    response = client.get("/v1/proposal", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    ids = {item["id"] for item in body["data"]["items"]}
    assert ids == {posted.id, offered.id}
    assert body["data"]["page"] == 1
    assert body["data"]["size"] == 20
    assert body["data"]["total"] == 2


def test_detail_hides_holding_and_allows_cancelled(client, db, auth_headers, sample_user):
    holding = make_proposal(db, sample_user.id, ProposalStatus.HOLDING)
    cancelled = make_proposal(db, sample_user.id, ProposalStatus.CANCELLED)

    holding_response = client.get(f"/v1/proposal/{holding.id}", headers=auth_headers)
    assert holding_response.status_code == 404
    assert holding_response.json()["error"]["code"] == "PROPOSAL_NOT_FOUND"

    cancelled_response = client.get(f"/v1/proposal/{cancelled.id}", headers=auth_headers)
    assert cancelled_response.status_code == 200
    assert cancelled_response.json()["data"]["status"] == "CANCELLED"


def test_list_own_returns_only_current_user_with_offers_and_status_filter(client, db, auth_headers, sample_user):
    other_user = make_user(db)
    own_posted = make_proposal(db, sample_user.id, ProposalStatus.POSTED)
    own_holding = make_proposal(db, sample_user.id, ProposalStatus.HOLDING)
    make_proposal(db, other_user.id, ProposalStatus.POSTED)

    old_offer = Offer(
        proposal_id=own_posted.id,
        runner_id=other_user.id,
        estimated_time=10,
        message="old",
        status=OfferStatus.WAITING,
    )
    new_offer = Offer(
        proposal_id=own_posted.id,
        runner_id=make_user(db, "01099990001").id,
        estimated_time=20,
        message="new",
        status=OfferStatus.REJECTED,
    )
    db.add_all([old_offer, new_offer])
    db.commit()

    response = client.get("/v1/proposal/own?status=POSTED", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()["data"]
    assert [item["id"] for item in items] == [own_posted.id]
    assert items[0]["ordererId"] == sample_user.id
    assert items[0]["offerCount"] == 2
    assert [offer["id"] for offer in items[0]["offers"]] == [new_offer.id, old_offer.id]

    all_own_response = client.get("/v1/proposal/own", headers=auth_headers)
    assert {item["id"] for item in all_own_response.json()["data"]} == {own_posted.id, own_holding.id}


def test_create_proposal_validates_contract_and_stores_holding(client, db, auth_headers, sample_user):
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


def test_update_proposal_author_and_status_rules(client, db, auth_headers, sample_user):
    other_user = make_user(db)
    holding = make_proposal(db, sample_user.id, ProposalStatus.HOLDING)
    posted = make_proposal(db, sample_user.id, ProposalStatus.POSTED)
    offered = make_proposal(db, sample_user.id, ProposalStatus.OFFERED)
    matched = make_proposal(db, sample_user.id, ProposalStatus.MATCHED)
    cancelled = make_proposal(db, sample_user.id, ProposalStatus.CANCELLED)

    forbidden = client.put(f"/v1/proposal/{holding.id}", json=proposal_payload(), headers=headers_for(other_user))
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

    for not_editable in [offered, matched, cancelled]:
        response = client.put(f"/v1/proposal/{not_editable.id}", json=proposal_payload(), headers=auth_headers)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "PROPOSAL_NOT_EDITABLE"

    missing = client.put("/v1/proposal/999999", json=proposal_payload(), headers=auth_headers)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "PROPOSAL_NOT_FOUND"


def test_cancel_proposal_author_status_rules_and_rejects_waiting_offers(client, db, auth_headers, sample_user):
    other_user = make_user(db)
    holding = make_proposal(db, sample_user.id, ProposalStatus.HOLDING)
    posted = make_proposal(db, sample_user.id, ProposalStatus.POSTED)
    offered = make_proposal(db, sample_user.id, ProposalStatus.OFFERED)
    matched = make_proposal(db, sample_user.id, ProposalStatus.MATCHED)
    cancelled = make_proposal(db, sample_user.id, ProposalStatus.CANCELLED)

    waiting_offer = Offer(
        proposal_id=offered.id,
        runner_id=other_user.id,
        estimated_time=10,
        status=OfferStatus.WAITING,
    )
    cancelled_offer = Offer(
        proposal_id=offered.id,
        runner_id=make_user(db, "01099990002").id,
        estimated_time=20,
        status=OfferStatus.REJECTED,
    )
    db.add_all([waiting_offer, cancelled_offer])
    db.commit()

    forbidden = client.post(f"/v1/proposal/{holding.id}/cancel", headers=headers_for(other_user))
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

    for not_cancellable in [matched, cancelled]:
        response = client.post(f"/v1/proposal/{not_cancellable.id}/cancel", headers=auth_headers)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "PROPOSAL_NOT_CANCELLABLE"


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
        "CANCELLED",
    }
    foreign_keys = inspect(db.bind).get_foreign_keys("proposals")
    assert foreign_keys == []
