from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.security import create_access_token
from app.models.mission import Mission, MissionStatus
from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.user import User


def headers_for(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': user.id})}"}


def make_user(db, phone: str, name: str = "Mission User") -> User:
    user = User(name=name, phone=phone, alarm_enabled=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_proposal(db, orderer_id: str, proposal_status: ProposalStatus = ProposalStatus.MATCHED) -> Proposal:
    deadline = datetime.now(timezone.utc) + timedelta(days=1)
    proposal = Proposal(
        orderer_id=orderer_id,
        title="미션 요청",
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


def make_mission(
    db,
    orderer: User,
    runner: User,
    status: MissionStatus = MissionStatus.CREATED,
) -> tuple[Mission, Offer]:
    proposal = make_proposal(db, orderer.id)
    offer = Offer(proposal_id=proposal.id, runner_id=runner.id, status=OfferStatus.ACCEPTED)
    db.add(offer)
    db.commit()
    db.refresh(offer)

    mission = Mission(
        proposal_id=proposal.id,
        offer_id=offer.id,
        orderer_id=orderer.id,
        runner_id=runner.id,
        status=status,
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission, offer


def test_get_mission_collection_endpoint_is_removed(client, sample_user):
    response = client.get("/v1/mission", headers=headers_for(sample_user))

    assert response.status_code == 404


def test_runner_complete_delivery(client, db, sample_user):
    runner = make_user(db, "01088880004")
    mission, _ = make_mission(db, sample_user, runner)

    response = client.post(
        f"/v1/mission/{mission.id}/complete-delivery",
        json={"proofImageUrl": "https://cdn.example/proof.jpg"},
        headers=headers_for(runner),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "전달 완료되었습니다."
    assert body["data"]["status"] == "DELIVERY_COMPLETED"
    assert body["data"]["deliveryProofImageUrl"] == "https://cdn.example/proof.jpg"

    db.refresh(mission)
    assert mission.status == MissionStatus.DELIVERY_COMPLETED
    assert mission.delivery_completed_at is not None


def test_delivery_then_receipt_completes_mission_and_offer(client, db, sample_user):
    runner = make_user(db, "01088880005")
    mission, offer = make_mission(db, sample_user, runner, MissionStatus.CREATED)

    delivery = client.post(
        f"/v1/mission/{mission.id}/complete-delivery",
        json={"proofImageUrl": "https://cdn.example/proof.jpg"},
        headers=headers_for(runner),
    )
    receipt = client.post(
        f"/v1/mission/{mission.id}/confirm-received",
        headers=headers_for(sample_user),
    )

    assert delivery.status_code == 200
    assert delivery.json()["data"]["status"] == "DELIVERY_COMPLETED"
    assert receipt.status_code == 200
    assert receipt.json()["data"]["status"] == "COMPLETED"

    db.refresh(mission)
    db.refresh(offer)
    assert mission.status == MissionStatus.COMPLETED
    assert mission.delivery_completed_at is not None
    assert mission.received_confirmed_at is not None
    assert offer.status == OfferStatus.COMPLETED


def test_update_mission_validation_author_and_state_errors(client, db, sample_user):
    runner = make_user(db, "01088880007")
    stranger = make_user(db, "01088880008")
    mission, _ = make_mission(db, sample_user, runner, MissionStatus.CREATED)
    completed, _ = make_mission(db, sample_user, runner, MissionStatus.COMPLETED)

    missing = client.post(
        "/v1/mission/999999/complete-delivery",
        json={"proofImageUrl": "https://cdn.example/proof.jpg"},
        headers=headers_for(runner),
    )
    forbidden = client.put(
        f"/v1/mission/{mission.id}",
        json={"action": "COMPLETE_DELIVERY", "proofImageUrl": "https://cdn.example/proof.jpg"},
        headers=headers_for(stranger),
    )
    wrong_actor = client.post(
        f"/v1/mission/{mission.id}/complete-delivery",
        json={"proofImageUrl": "https://cdn.example/proof.jpg"},
        headers=headers_for(sample_user),
    )
    proof_optional = client.post(
        f"/v1/mission/{mission.id}/complete-delivery",
        json={},
        headers=headers_for(runner),
    )
    not_updatable = client.post(
        f"/v1/mission/{completed.id}/complete-delivery",
        json={"proofImageUrl": "https://cdn.example/proof.jpg"},
        headers=headers_for(runner),
    )
    deprecated_start = client.put(
        f"/v1/mission/{mission.id}",
        json={"action": "START_PROGRESS"},
        headers=headers_for(runner),
    )

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "MISSION_NOT_FOUND"
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"
    assert wrong_actor.status_code == 403
    assert wrong_actor.json()["error"]["code"] == "FORBIDDEN"
    assert proof_optional.status_code == 200
    assert proof_optional.json()["data"]["status"] == "DELIVERY_COMPLETED"
    assert proof_optional.json()["data"]["deliveryProofImageUrl"] is None
    assert not_updatable.status_code == 409
    assert not_updatable.json()["error"]["code"] == "MISSION_NOT_UPDATABLE"
    assert deprecated_start.status_code == 400
    assert deprecated_start.json()["error"]["code"] == "VALIDATION_ERROR"


def test_dispute_requires_reason_and_allows_mission_actor(client, db, sample_user):
    runner = make_user(db, "01088880009")
    mission, _ = make_mission(db, sample_user, runner, MissionStatus.CREATED)

    missing_reason = client.post(
        f"/v1/mission/{mission.id}/dispute",
        json={},
        headers=headers_for(sample_user),
    )
    disputed = client.post(
        f"/v1/mission/{mission.id}/dispute",
        json={"disputeReason": "물품이 다릅니다."},
        headers=headers_for(runner),
    )

    assert missing_reason.status_code == 400
    assert missing_reason.json()["error"]["code"] == "VALIDATION_ERROR"
    assert disputed.status_code == 200
    assert disputed.json()["data"]["status"] == "DISPUTED"
    assert disputed.json()["data"]["disputeReason"] == "물품이 다릅니다."


def test_deprecated_update_mission_delegates_supported_actions(client, db, sample_user):
    runner = make_user(db, "01088880010")
    mission, offer = make_mission(db, sample_user, runner, MissionStatus.CREATED)

    delivery = client.put(
        f"/v1/mission/{mission.id}",
        json={"action": "COMPLETE_DELIVERY", "proofImageUrl": "https://cdn.example/proof.jpg"},
        headers=headers_for(runner),
    )
    receipt = client.put(
        f"/v1/mission/{mission.id}",
        json={"action": "CONFIRM_RECEIVED"},
        headers=headers_for(sample_user),
    )

    assert delivery.status_code == 200
    assert delivery.json()["data"]["status"] == "DELIVERY_COMPLETED"
    assert receipt.status_code == 200
    assert receipt.json()["data"]["status"] == "COMPLETED"

    db.refresh(mission)
    db.refresh(offer)
    assert mission.status == MissionStatus.COMPLETED
    assert offer.status == OfferStatus.COMPLETED
