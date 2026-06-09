"""Pytest configuration and fixtures for user/auth flows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Generator
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.routing import Match

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.user import User
from app.services.sms_service import get_sms_sender


@dataclass
class RecordingSmsSender:
    sent_messages: list[dict] = field(default_factory=list)

    def send(self, phone: str, message: str) -> None:
        self.sent_messages.append({"phone": phone, "message": message})


class NoopNotificationWorker:
    def flush_pending(self, db_factory):
        _ = db_factory

    def retry_failed(self, db_factory):
        _ = db_factory


class OpenApiAssertingClient:
    def __init__(self, client: TestClient):
        self._client = client

    def __getattr__(self, name: str):
        return getattr(self._client, name)

    def get(self, url: str, **kwargs) -> Response:
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> Response:
        return self._request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> Response:
        return self._request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs) -> Response:
        return self._request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs) -> Response:
        return self._request("DELETE", url, **kwargs)

    def _request(self, method: str, url: str, **kwargs) -> Response:
        response = self._client.request(method, url, **kwargs)
        _assert_response_matches_openapi(method, url, response)
        return response


def _assert_response_matches_openapi(method: str, url: str, response: Response) -> None:
    path_template = _find_openapi_path(method, url)
    if path_template is None:
        return

    schema = app.openapi()
    operation = schema["paths"][path_template][method.lower()]
    status_code = str(response.status_code)
    assert status_code in operation["responses"], f"{method} {path_template} missing OpenAPI response {status_code}"

    documented_response = operation["responses"][status_code]
    if response.status_code == 204:
        assert response.content == b""
        assert "content" not in documented_response
        return

    if "application/json" not in response.headers.get("content-type", ""):
        return

    actual = response.json()
    content = documented_response.get("content", {}).get("application/json")
    assert content is not None, f"{method} {path_template} {status_code} missing JSON OpenAPI content"

    if 200 <= response.status_code < 300:
        examples = _success_examples(content)
        assert examples, f"{method} {path_template} {status_code} has no success examples"
        matching_examples = [
            example
            for example in examples
            if _compatible_shape(actual, example)
            and (
                not isinstance(actual, dict)
                or "message" not in actual
                or "message" not in example
                or actual["message"] == example["message"]
            )
        ]
        assert matching_examples, f"{method} {path_template} {status_code} has no matching success example"
        _assert_success_example_contract(actual, matching_examples[0], method, path_template, status_code)
        return

    examples = content.get("examples", {})
    error_code = actual.get("error", {}).get("code")
    assert error_code, f"{method} {path_template} {status_code} error response has no error.code"

    matching_examples = [example["value"] for example in examples.values() if example["value"]["error"]["code"] == error_code]
    message_matches = [
        example for example in matching_examples if example["error"]["message"] == actual["error"]["message"]
    ]
    if message_matches:
        matching_examples = message_matches
    assert matching_examples, f"{method} {path_template} {status_code} has no OpenAPI example for {error_code}"
    _assert_error_example_contract(actual, matching_examples[0], method, path_template, status_code)


def _success_examples(content: dict) -> list:
    if "example" in content:
        return [content["example"]]
    return [example["value"] for example in content.get("examples", {}).values()]


def _assert_success_example_contract(actual, example, method: str, path: str, status_code: str) -> None:
    assert _compatible_shape(actual, example), f"{method} {path} {status_code} success example shape mismatch"

    if isinstance(actual, dict) and "success" in actual:
        assert actual["success"] == example["success"]
    if isinstance(actual, dict) and "message" in actual and "message" in example:
        assert actual["message"] == example["message"]


def _assert_error_example_contract(actual, example, method: str, path: str, status_code: str) -> None:
    assert set(actual) == set(example), f"{method} {path} {status_code} error example shape mismatch"
    assert set(actual["error"]) == set(example["error"])
    assert actual["success"] is False
    assert actual["error"]["code"] == example["error"]["code"]
    assert actual["error"]["message"] == example["error"]["message"]
    assert "details" in actual["error"]
    assert "timestamp" in actual


def _shape(value):
    if isinstance(value, dict):
        return {key: _shape(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_shape(value[0])] if value else []
    if value is None:
        return None
    if isinstance(value, bool):
        return bool
    if isinstance(value, int):
        return int
    if isinstance(value, float):
        return float
    if isinstance(value, str):
        return str
    if isinstance(value, datetime):
        return str
    if isinstance(value, Enum):
        return str
    return type(value)


def _compatible_shape(actual, example) -> bool:
    if isinstance(actual, dict) and isinstance(example, dict):
        for key, value in actual.items():
            if key not in example:
                if value is None:
                    continue
                return False
            if not _compatible_shape(value, example[key]):
                return False
        for key, value in example.items():
            if key not in actual:
                if value is None:
                    continue
                return False
        return True
    if isinstance(actual, list) and isinstance(example, list):
        if not actual or not example:
            return True
        return _compatible_shape(actual[0], example[0])
    if actual is None or example is None:
        if isinstance(actual, (dict, list)) or isinstance(example, (dict, list)):
            return False
        return actual is None or example is None
    return _shape(actual) == _shape(example)


def _find_openapi_path(method: str, url: str) -> str | None:
    path = urlsplit(url).path
    scope = {"type": "http", "path": path, "method": method}
    for route in app.routes:
        route_methods = getattr(route, "methods", None)
        if route_methods and method not in route_methods:
            continue
        match, _ = route.matches(scope)
        if match == Match.FULL:
            return getattr(route, "path", None)
    return None


_test_db_url = (
    f"mysql+pymysql://{settings.db_username}:{settings.db_password}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}_test"
    f"?charset=utf8mb4"
)

TEST_ENGINE = create_engine(_test_db_url)
assert TEST_ENGINE.dialect.name == "mysql", "Tests must use MySQL"

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture(scope="function")
def sms_sender() -> RecordingSmsSender:
    return RecordingSmsSender()


@pytest.fixture(scope="function")
def client(db: Session, sms_sender: RecordingSmsSender, monkeypatch: pytest.MonkeyPatch) -> OpenApiAssertingClient:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_sms_sender] = lambda: sms_sender
    monkeypatch.setattr("app.api.v1.offer.get_notification_worker", lambda: NoopNotificationWorker())

    with TestClient(app) as test_client:
        yield OpenApiAssertingClient(test_client)

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db: Session) -> User:
    user = User(
        name="Test User",
        phone="01012345678",
        phone_verified_at=None,
        last_login_at=None,
        alarm_enabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(sample_user: User) -> dict:
    access_token = create_access_token({"sub": str(sample_user.id)})
    return {"Authorization": f"Bearer {access_token}"}
