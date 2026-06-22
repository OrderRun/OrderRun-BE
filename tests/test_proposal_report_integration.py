from __future__ import annotations

from app.models.offer import Offer, OfferStatus
from app.models.proposal import ProposalStatus
from app.models.proposal_report import ProposalReport, ProposalReportReasonQuestion, ProposalReportStatus


REASONS = (
    "광고 또는 스팸이에요",
    "욕설이나 혐오 표현이 있어요",
    "거짓 정보 같아요",
    "부적절한 사진이나 내용이에요",
    "기타",
)


def seed_reasons(db) -> list[ProposalReportReasonQuestion]:
    reasons = [
        ProposalReportReasonQuestion(question_text=text, display_order=index, is_active=True)
        for index, text in enumerate(REASONS, start=1)
    ]
    db.add_all(reasons)
    db.commit()
    return reasons


def test_list_proposal_report_reasons_returns_active_ordered_questions(client, db, auth_headers):
    reasons = seed_reasons(db)
    db.add(ProposalReportReasonQuestion(question_text="비활성", display_order=6, is_active=False))
    db.commit()

    response = client.get("/v1/proposal-report-reasons", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"] == [
        {"id": reason.id, "questionText": reason.question_text, "displayOrder": reason.display_order}
        for reason in reasons
    ]


def test_create_proposal_report_validates_public_target_reporter_and_duplicate(client, db, factory, auth_headers, sample_user):
    reason = seed_reasons(db)[0]
    proposal = factory.proposal(sample_user.id, ProposalStatus.POSTED)
    reporter = factory.user("01055550001")
    headers = factory.headers_for(reporter)

    response = client.post(
        f"/v1/proposal/{proposal.id}/reports",
        headers=headers,
        json={"reasonQuestionId": reason.id, "detailReason": "반복 광고입니다."},
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["status"] == "PENDING"
    assert data["reporterId"] == reporter.id
    assert data["reasonQuestionText"] == REASONS[0]
    assert data["detailReason"] == "반복 광고입니다."

    duplicate = client.post(f"/v1/proposal/{proposal.id}/reports", headers=headers, json={"reasonQuestionId": reason.id})
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE_PROPOSAL_REPORT"

    self_report = client.post(f"/v1/proposal/{proposal.id}/reports", headers=auth_headers, json={"reasonQuestionId": reason.id})
    assert self_report.status_code == 403
    assert self_report.json()["error"]["code"] == "PROPOSAL_SELF_REPORT_NOT_ALLOWED"

    closed = factory.proposal(sample_user.id, ProposalStatus.MATCHED)
    closed_response = client.post(f"/v1/proposal/{closed.id}/reports", headers=headers, json={"reasonQuestionId": reason.id})
    assert closed_response.status_code == 409
    assert closed_response.json()["error"]["code"] == "PROPOSAL_NOT_REPORTABLE"

    invalid_reason = client.post(f"/v1/proposal/{proposal.id}/reports", headers=factory.headers_for(factory.user("01055550002")), json={"reasonQuestionId": 999})
    assert invalid_reason.status_code == 400


def test_accept_proposal_report_marks_proposal_reported_and_rejects_waiting_offers(client, db, factory, sample_user):
    reason = seed_reasons(db)[0]
    proposal = factory.proposal(sample_user.id, ProposalStatus.OFFERED)
    waiting_runner = factory.user("01055550003")
    factory.offer(proposal.id, waiting_runner.id, OfferStatus.WAITING)
    reporter = factory.user("01055550004")
    report = ProposalReport(
        proposal_id=proposal.id,
        reporter_id=reporter.id,
        reason_question_id=reason.id,
        status=ProposalReportStatus.PENDING,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    response = client.post(f"/v1/admin/proposal-reports/{report.id}/accept")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ACCEPTED"
    db.refresh(proposal)
    assert proposal.status == ProposalStatus.REPORTED
    offer = db.query(Offer).filter_by(proposal_id=proposal.id).one()
    assert offer.status == OfferStatus.REJECTED
    public = client.get("/v1/proposal", headers=factory.headers_for(reporter))
    assert proposal.id not in {item["id"] for item in public.json()["data"]["content"]}


def test_admin_can_reject_report_and_cannot_review_report_twice(client, db, factory, sample_user):
    reason = seed_reasons(db)[0]
    proposal = factory.proposal(sample_user.id, ProposalStatus.POSTED)
    reporter = factory.user("01055550005")
    report = ProposalReport(proposal_id=proposal.id, reporter_id=reporter.id, reason_question_id=reason.id)
    db.add(report)
    db.commit()
    db.refresh(report)

    listing = client.get("/v1/admin/proposal-reports?status=PENDING")
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()["data"]["content"]] == [report.id]

    rejected = client.post(f"/v1/admin/proposal-reports/{report.id}/reject")
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == "REJECTED"
    db.refresh(proposal)
    assert proposal.status == ProposalStatus.POSTED

    again = client.post(f"/v1/admin/proposal-reports/{report.id}/accept")
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "PROPOSAL_REPORT_NOT_REVIEWABLE"
