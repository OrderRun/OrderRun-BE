from __future__ import annotations

from datetime import datetime, timezone

from app.models.dispute_evidence import DisputeEvidence
from app.models.dispute_survey import DisputeSurveyQuestion, DisputeSurveyTargetType
from app.models.offer import OfferStatus
from app.models.proposal import ProposalStatus


def dispute_question(target_type: DisputeSurveyTargetType) -> DisputeSurveyQuestion:
    return DisputeSurveyQuestion(
        target_type=target_type,
        question_text="분쟁 사유를 선택해주세요.",
        display_order=1,
        is_active=True,
    )


def create_runner_dispute(client, db, factory, orderer, runner) -> tuple[int, int, DisputeEvidence]:
    proposal, offer = factory.execution(orderer, runner, ProposalStatus.MATCHED, OfferStatus.ACCEPTED)
    offer.accepted_at = datetime.now(timezone.utc)
    question = dispute_question(DisputeSurveyTargetType.RUNNER)
    db.add(question)
    db.commit()

    response = client.post(
        f"/v1/offer/{offer.id}/dispute",
        json={"surveyQuestionId": question.id, "disputeReason": "배송 중 파손"},
        headers=factory.headers_for(runner),
    )
    assert response.status_code == 200
    evidence = db.query(DisputeEvidence).filter(DisputeEvidence.offer_id == offer.id).one()
    return proposal.id, offer.id, evidence


def test_get_dispute_evidence_by_proposal_id_allows_participants(client, db, factory):
    orderer = factory.user("01088880001")
    runner = factory.user("01088880002")
    proposal_id, _, evidence = create_runner_dispute(client, db, factory, orderer, runner)

    orderer_response = client.get(
        f"/v1/dispute-evidence?proposalId={proposal_id}",
        headers=factory.headers_for(orderer),
    )
    runner_response = client.get(
        f"/v1/dispute-evidence?proposalId={proposal_id}",
        headers=factory.headers_for(runner),
    )

    assert orderer_response.status_code == 200
    assert runner_response.status_code == 200
    assert orderer_response.json()["data"] == {
        "id": evidence.id,
        "proposalId": proposal_id,
        "offerId": evidence.offer_id,
        "actorId": runner.id,
        "reason": "배송 중 파손",
        "surveyQuestionId": evidence.survey_question_id,
        "createdAt": orderer_response.json()["data"]["createdAt"],
    }
    assert runner_response.json()["data"]["id"] == evidence.id


def test_get_dispute_evidence_by_offer_id_allows_participants(client, db, factory):
    orderer = factory.user("01088880003")
    runner = factory.user("01088880004")
    _, offer_id, evidence = create_runner_dispute(client, db, factory, orderer, runner)

    orderer_response = client.get(
        f"/v1/dispute-evidence?offerId={offer_id}",
        headers=factory.headers_for(orderer),
    )
    runner_response = client.get(
        f"/v1/dispute-evidence?offerId={offer_id}",
        headers=factory.headers_for(runner),
    )

    assert orderer_response.status_code == 200
    assert runner_response.status_code == 200
    assert orderer_response.json()["data"]["id"] == evidence.id
    assert runner_response.json()["data"]["id"] == evidence.id


def test_get_dispute_evidence_rejects_non_participant_and_invalid_query(client, db, factory):
    orderer = factory.user("01088880005")
    runner = factory.user("01088880006")
    stranger = factory.user("01088880007")
    proposal_id, offer_id, _ = create_runner_dispute(client, db, factory, orderer, runner)

    forbidden = client.get(
        f"/v1/dispute-evidence?proposalId={proposal_id}",
        headers=factory.headers_for(stranger),
    )
    missing_query = client.get("/v1/dispute-evidence", headers=factory.headers_for(orderer))
    duplicate_query = client.get(
        f"/v1/dispute-evidence?proposalId={proposal_id}&offerId={offer_id}",
        headers=factory.headers_for(orderer),
    )

    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"
    assert missing_query.status_code == 400
    assert missing_query.json()["error"]["code"] == "VALIDATION_ERROR"
    assert duplicate_query.status_code == 400
    assert duplicate_query.json()["error"]["code"] == "VALIDATION_ERROR"


def test_get_dispute_evidence_returns_not_found(client, db, factory):
    orderer = factory.user("01088880008")
    proposal = factory.proposal(orderer.id, ProposalStatus.MATCHED)

    response = client.get(
        f"/v1/dispute-evidence?proposalId={proposal.id}",
        headers=factory.headers_for(orderer),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DISPUTE_EVIDENCE_NOT_FOUND"
