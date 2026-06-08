from __future__ import annotations

import ast
from pathlib import Path

from app.main import app


ALLOWED_SCHEMA_BASES = {"BaseModel", "Generic", "str", "Enum"}


def test_openapi_contains_korean_api_metadata():
    schema = app.openapi()

    assert schema["info"]["title"] == "OrderRun API"
    assert "OrderRun 백엔드 API" in schema["info"]["description"]


def test_auth_signup_send_openapi_examples_match_response_shape():
    operation = app.openapi()["paths"]["/v1/auth/signup/send"]["post"]

    assert operation["summary"] == "회원가입 인증번호 발송"

    success_example = operation["responses"]["200"]["content"]["application/json"]["example"]
    assert success_example == {
        "success": True,
        "data": {"phone": "01012345678", "expiresAt": "2026-06-01T12:05:00+09:00"},
    }

    conflict_examples = operation["responses"]["409"]["content"]["application/json"]["examples"]
    phone_exists = conflict_examples["PHONE_ALREADY_EXISTS"]["value"]
    assert phone_exists == {
        "success": False,
        "error": {
            "code": "PHONE_ALREADY_EXISTS",
            "message": "Phone number already exists",
            "details": None,
        },
        "timestamp": "2026-06-01T12:00:00+09:00",
    }


def test_validation_error_openapi_example_uses_standard_error_wrapper():
    operation = app.openapi()["paths"]["/v1/auth/login/confirm"]["post"]

    validation_example = operation["responses"]["400"]["content"]["application/json"]["examples"][
        "VALIDATION_ERROR"
    ]["value"]

    assert validation_example["success"] is False
    assert validation_example["error"]["code"] == "VALIDATION_ERROR"
    assert validation_example["timestamp"] == "2026-06-01T12:00:00+09:00"


def test_openapi_operations_have_success_examples_and_standard_error_examples():
    schema = app.openapi()

    for path, path_item in schema["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue

            responses = operation["responses"]
            assert "422" not in responses, f"{method.upper()} {path} documents FastAPI's default 422"

            success_codes = [code for code in responses if code.startswith("2")]
            assert success_codes, f"{method.upper()} {path} has no 2xx response"

            for code in success_codes:
                content = responses[code].get("content", {}).get("application/json")
                if code == "204":
                    assert content is None, f"{method.upper()} {path} 204 must not document a JSON body"
                    continue

                assert content is not None, f"{method.upper()} {path} {code} has no JSON content"
                assert "example" in content or "examples" in content, (
                    f"{method.upper()} {path} {code} has no success example"
                )

            for code, response in responses.items():
                if not code.startswith(("4", "5")):
                    continue
                content = response.get("content", {}).get("application/json")
                assert content is not None, f"{method.upper()} {path} {code} has no JSON content"
                assert "examples" in content, f"{method.upper()} {path} {code} has no error examples"
                for example in content["examples"].values():
                    value = example["value"]
                    assert value["success"] is False
                    assert set(value["error"]) == {"code", "message", "details"}
                    assert value["error"]["code"]
                    assert value["error"]["message"]
                    assert value["timestamp"] == "2026-06-01T12:00:00+09:00"


def test_representative_success_examples_match_contracts():
    schema = app.openapi()

    proposal_create = schema["paths"]["/v1/proposal"]["post"]["responses"]["201"]["content"]["application/json"][
        "example"
    ]
    assert proposal_create["message"] == "요청이 등록되었습니다."
    assert proposal_create["data"]["status"] == "HOLDING"
    assert set(proposal_create["data"]) == {"id", "title", "content", "deadline", "errandFee", "status"}

    offer_accept = schema["paths"]["/v1/offer/{offer_id}/accept"]["post"]["responses"]["201"]["content"][
        "application/json"
    ]["example"]
    assert offer_accept["message"] == "제안이 수락되었습니다."
    assert offer_accept["data"]["proposalStatus"] == "MATCHED"
    assert offer_accept["data"]["missionStatus"] == "CREATED"
    assert {"runFee", "itemPrice", "totalAmount"}.isdisjoint(offer_accept["data"])

    proposal_detail_examples = schema["paths"]["/v1/proposal/{proposal_id}"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["examples"]
    assert proposal_detail_examples["without_mission"]["value"]["data"]["missionId"] is None
    assert proposal_detail_examples["with_mission"]["value"]["data"]["missionId"] == 100

    offer_detail_examples = schema["paths"]["/v1/offer/{offer_id}"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["examples"]
    assert offer_detail_examples["without_mission"]["value"]["data"]["missionId"] is None
    assert offer_detail_examples["with_mission"]["value"]["data"]["missionId"] == 100

    mission_delivery = schema["paths"]["/v1/mission/{mission_id}/complete-delivery"]["post"]["responses"]["200"][
        "content"
    ]["application/json"]["example"]
    assert mission_delivery["message"] == "전달 완료되었습니다."
    assert mission_delivery["data"]["status"] == "DELIVERY_COMPLETED"
    assert mission_delivery["data"]["deliveryProofImageUrl"] == "https://cdn.example/proof.jpg"

    settlement = schema["paths"]["/v1/settlement/account"]["put"]["responses"]["200"]["content"]["application/json"][
        "example"
    ]
    assert settlement["message"] == "정산 계좌가 저장되었습니다."
    assert settlement["data"]["maskedAccountNumber"] == "********9012"

    notification = schema["paths"]["/api/v1/notifications/{notification_id}"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["example"]
    assert notification["notification_type"] == "custom"
    assert notification["status"] == "sent"


def test_auth_login_confirm_request_exposes_explicit_fields():
    schema = app.openapi()["components"]["schemas"]["AuthLoginConfirmRequest"]

    assert set(schema["properties"]) == {"phone", "code", "fcmToken"}


def test_admin_confirm_payment_has_no_request_body():
    operation = app.openapi()["paths"]["/api/v1/admin/proposal/{proposal_id}/confirm-payment"]["post"]

    assert "requestBody" not in operation


def test_offer_accept_has_no_request_body_or_amount_response_fields():
    operation = app.openapi()["paths"]["/v1/offer/{offer_id}/accept"]["post"]

    assert "requestBody" not in operation
    response_ref = operation["responses"]["201"]["content"]["application/json"]["schema"]["$ref"]
    response_name = response_ref.rsplit("/", 1)[-1]
    data_schema = app.openapi()["components"]["schemas"][response_name]["properties"]["data"]
    accept_ref = next(item["$ref"] for item in data_schema["anyOf"] if "$ref" in item)
    accept_name = accept_ref.rsplit("/", 1)[-1]
    accept_schema = app.openapi()["components"]["schemas"][accept_name]

    assert {"runFee", "itemPrice", "totalAmount"}.isdisjoint(accept_schema["properties"])


def test_mission_collection_get_is_not_documented():
    mission_collection = app.openapi()["paths"].get("/v1/mission")

    assert mission_collection is None or "get" not in mission_collection


def test_list_status_filters_are_repeatable_array_query_parameters():
    schema = app.openapi()
    targets = [
        ("/v1/proposal", "get"),
        ("/v1/proposal/own", "get"),
        ("/v1/offer", "get"),
        ("/v1/offer/own", "get"),
    ]

    for path, method in targets:
        operation = schema["paths"][path][method]
        status_param = next(parameter for parameter in operation["parameters"] if parameter["name"] == "status")
        array_schema = next(item for item in status_param["schema"]["anyOf"] if item.get("type") == "array")

        assert status_param["in"] == "query"
        assert array_schema["items"]["$ref"].startswith("#/components/schemas/")
        assert "status=A&status=B" in status_param["description"]


def test_api_schemas_do_not_inherit_from_other_api_dtos():
    schema_dir = Path(__file__).resolve().parents[1] / "app" / "schemas"
    violations: list[str] = []

    for path in schema_dir.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for base in node.bases:
                base_name = _base_name(base)
                if base_name and base_name not in ALLOWED_SCHEMA_BASES:
                    violations.append(f"{path.name}:{node.name}({base_name})")

    assert violations == []


def _base_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return None
