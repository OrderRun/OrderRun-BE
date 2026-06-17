from __future__ import annotations

from app.models.dispute_survey import DisputeSurveyQuestion, DisputeSurveyTargetType


def _question(
    target_type: DisputeSurveyTargetType,
    question_text: str,
    display_order: int,
    is_active: bool = True,
) -> DisputeSurveyQuestion:
    return DisputeSurveyQuestion(
        target_type=target_type,
        question_text=question_text,
        display_order=display_order,
        is_active=is_active,
    )


def test_list_order_dispute_survey_questions_returns_active_questions_in_display_order(client, db, auth_headers):
    older = _question(DisputeSurveyTargetType.ORDER, "두 번째 오더 질문", 2)
    first = _question(DisputeSurveyTargetType.ORDER, "첫 번째 오더 질문", 1)
    runner = _question(DisputeSurveyTargetType.RUNNER, "러너 질문", 1)
    inactive = _question(DisputeSurveyTargetType.ORDER, "비활성 질문", 3, is_active=False)
    db.add_all([older, first, runner, inactive])
    db.commit()

    response = client.get("/v1/dispute-survey/questions?targetType=ORDER", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Success"
    assert [item["questionText"] for item in body["data"]] == ["첫 번째 오더 질문", "두 번째 오더 질문"]
    assert [item["displayOrder"] for item in body["data"]] == [1, 2]
    assert {item["targetType"] for item in body["data"]} == {"ORDER"}


def test_list_runner_dispute_survey_questions_returns_runner_questions_only(client, db, auth_headers):
    db.add_all(
        [
            _question(DisputeSurveyTargetType.ORDER, "오더 질문", 1),
            _question(DisputeSurveyTargetType.RUNNER, "첫 번째 러너 질문", 1),
            _question(DisputeSurveyTargetType.RUNNER, "두 번째 러너 질문", 2),
        ]
    )
    db.commit()

    response = client.get("/v1/dispute-survey/questions?targetType=RUNNER", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert [item["questionText"] for item in body["data"]] == ["첫 번째 러너 질문", "두 번째 러너 질문"]
    assert {item["targetType"] for item in body["data"]} == {"RUNNER"}


def test_list_dispute_survey_questions_returns_empty_list(client, auth_headers):
    response = client.get("/v1/dispute-survey/questions?targetType=ORDER", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": [], "message": "Success"}


def test_list_dispute_survey_questions_validation_and_auth_errors(client, auth_headers):
    invalid_target = client.get("/v1/dispute-survey/questions?targetType=CUSTOMER", headers=auth_headers)
    assert invalid_target.status_code == 400
    assert invalid_target.json()["error"]["code"] == "VALIDATION_ERROR"

    no_token = client.get("/v1/dispute-survey/questions?targetType=ORDER")
    assert no_token.status_code == 401
    assert no_token.json()["error"]["code"] == "INVALID_TOKEN"


def test_dispute_survey_question_model_spec_matches_plan():
    table = DisputeSurveyQuestion.__table__

    assert str(table.c.id.type).upper() == "BIGINT"
    assert str(table.c.target_type.type).upper() == "VARCHAR(6)"
    assert str(table.c.question_text.type).upper() == "VARCHAR(500)"
    assert table.c.is_active.nullable is False
    assert table.foreign_keys == set()

    unique_names = {constraint.name for constraint in table.constraints}
    index_names = {index.name for index in table.indexes}
    assert "uk_dispute_survey_questions_target_order" in unique_names
    assert "idx_dispute_survey_questions_lookup" in index_names
