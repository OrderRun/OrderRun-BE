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


def test_auth_login_confirm_request_exposes_explicit_fields():
    schema = app.openapi()["components"]["schemas"]["AuthLoginConfirmRequest"]

    assert set(schema["properties"]) == {"phone", "code", "fcmToken"}


def test_admin_confirm_payment_has_no_request_body():
    operation = app.openapi()["paths"]["/api/v1/admin/proposal/{proposal_id}/confirm-payment"]["post"]

    assert "requestBody" not in operation


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
