from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.security import create_access_token
from app.models.offer import Offer, OfferStatus
from app.models.proof import Proof, ProofType
from app.models.proposal import Proposal, ProposalStatus
from app.models.user import User


def headers_for(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': user.id})}"}


def make_user(db, phone: str, name: str = "Execution User") -> User:
    user = User(name=name, phone=phone, alarm_enabled=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_proposal(db, orderer_id: str, proposal_status: ProposalStatus = ProposalStatus.MATCHED) -> Proposal:
    deadline = datetime.now(timezone.utc) + timedelta(days=1)
    proposal = Proposal(
        orderer_id=orderer_id,
        title="수행 요청",
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


def make_execution(
    db,
    orderer: User,
    runner: User,
    proposal_status: ProposalStatus = ProposalStatus.MATCHED,
    offer_status: OfferStatus = OfferStatus.ACCEPTED,
) -> tuple[Proposal, Offer]:
    proposal = make_proposal(db, orderer.id, proposal_status)
    offer = Offer(proposal_id=proposal.id, runner_id=runner.id, status=offer_status)
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return proposal, offer


def test_mission_api_endpoints_are_removed(client, sample_user):
    headers = headers_for(sample_user)

    assert client.get("/v1/mission", headers=headers).status_code == 404
    assert client.post("/v1/mission/1/complete-delivery", json={}, headers=headers).status_code == 404
    assert client.post("/v1/mission/1/confirm-received", headers=headers).status_code == 404
    assert client.post("/v1/mission/1/dispute", json={"disputeReason": "x"}, headers=headers).status_code == 404
    assert client.put("/v1/mission/1", json={"action": "COMPLETE_DELIVERY"}, headers=headers).status_code == 404


def test_runner_complete_delivery_updates_offer_proposal_and_creates_proof(client, db, sample_user):
    runner = make_user(db, "01088880004")
    proposal, offer = make_execution(db, sample_user, runner)

    response = client.post(
        f"/v1/offer/{offer.id}/complete-delivery",
        json={"proofImageUrl": "https://cdn.example/proof.jpg"},
        headers=headers_for(runner),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "전달 완료되었습니다."
    assert body["data"]["status"] == "DELIVERY_COMPLETED"
    assert "missionId" not in body["data"]
    assert body["data"]["deliveryCompletedAt"] is not None

    db.refresh(proposal)
    db.refresh(offer)
    proof = db.query(Proof).filter(Proof.offer_id == offer.id, Proof.proof_type == ProofType.DELIVERY).one()
    assert offer.status == OfferStatus.DELIVERY_COMPLETED
    assert proposal.status == ProposalStatus.DELIVERY_REPORTED
    assert offer.delivery_completed_at is not None
    assert proposal.delivery_reported_at is not None
    assert proof.actor_id == runner.id
    assert proof.image_url == "https://cdn.example/proof.jpg"


def test_delivery_then_receipt_updates_role_status_timestamps(client, db, sample_user):
    runner = make_user(db, "01088880005")
    proposal, offer = make_execution(db, sample_user, runner)

    delivery = client.post(
        f"/v1/offer/{offer.id}/complete-delivery",
        json={"proofImageUrl": "https://cdn.example/proof.jpg"},
        headers=headers_for(runner),
    )
    receipt = client.post(
        f"/v1/proposal/{proposal.id}/confirm-received",
        headers=headers_for(sample_user),
    )

    assert delivery.status_code == 200
    assert delivery.json()["data"]["status"] == "DELIVERY_COMPLETED"
    assert receipt.status_code == 200
    assert receipt.json()["data"]["status"] == "RECEIVED_CONFIRMED"
    assert receipt.json()["data"]["receivedConfirmedAt"] is not None

    db.refresh(proposal)
    db.refresh(offer)
    assert proposal.status == ProposalStatus.RECEIVED_CONFIRMED
    assert offer.status == OfferStatus.RECEIPT_CONFIRMED
    assert proposal.received_confirmed_at is not None
    assert offer.receipt_confirmed_at is not None


def test_action_validation_author_and_state_errors(client, db, sample_user):
    runner = make_user(db, "01088880007")
    stranger = make_user(db, "01088880008")
    proposal, offer = make_execution(db, sample_user, runner)
    completed, completed_offer = make_execution(
        db,
        sample_user,
        runner,
        ProposalStatus.RECEIVED_CONFIRMED,
        OfferStatus.RECEIPT_CONFIRMED,
    )

    missing = client.post(
        "/v1/offer/999999/complete-delivery",
        json={"proofImageUrl": "https://cdn.example/proof.jpg"},
        headers=headers_for(runner),
    )
    forbidden = client.post(
        f"/v1/offer/{offer.id}/complete-delivery",
        json={"proofImageUrl": "https://cdn.example/proof.jpg"},
        headers=headers_for(stranger),
    )
    wrong_actor = client.post(
        f"/v1/proposal/{proposal.id}/confirm-received",
        headers=headers_for(stranger),
    )
    proof_optional = client.post(
        f"/v1/offer/{offer.id}/complete-delivery",
        json={},
        headers=headers_for(runner),
    )
    not_updatable = client.post(
        f"/v1/offer/{completed_offer.id}/complete-delivery",
        json={"proofImageUrl": "https://cdn.example/proof.jpg"},
        headers=headers_for(runner),
    )

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "OFFER_NOT_FOUND"
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"
    assert wrong_actor.status_code == 403
    assert wrong_actor.json()["error"]["code"] == "FORBIDDEN"
    assert proof_optional.status_code == 200
    assert proof_optional.json()["data"]["status"] == "DELIVERY_COMPLETED"
    assert not_updatable.status_code == 409
    assert not_updatable.json()["error"]["code"] == "OFFER_NOT_UPDATABLE"
    assert completed.id


def test_dispute_requires_reason_and_allows_role_specific_routes(client, db, sample_user):
    runner = make_user(db, "01088880009")
    proposal, offer = make_execution(db, sample_user, runner)

    missing_reason = client.post(
        f"/v1/proposal/{proposal.id}/dispute",
        json={},
        headers=headers_for(sample_user),
    )
    disputed_by_runner = client.post(
        f"/v1/offer/{offer.id}/dispute",
        json={"disputeReason": "물품이 다릅니다."},
        headers=headers_for(runner),
    )

    assert missing_reason.status_code == 400
    assert missing_reason.json()["error"]["code"] == "VALIDATION_ERROR"
    assert disputed_by_runner.status_code == 200
    assert disputed_by_runner.json()["data"]["status"] == "DISPUTED"
    assert disputed_by_runner.json()["data"]["disputedAt"] is not None

    db.refresh(proposal)
    db.refresh(offer)
    proof = db.query(Proof).filter(Proof.offer_id == offer.id, Proof.proof_type == ProofType.DISPUTE).one()
    assert proposal.status == ProposalStatus.DISPUTED
    assert offer.status == OfferStatus.DISPUTED
    assert proposal.disputed_at is not None
    assert offer.disputed_at is not None
    assert proof.actor_id == runner.id
    assert proof.reason == "물품이 다릅니다."
