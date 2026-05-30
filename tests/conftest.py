"""Pytest configuration and fixtures for user/auth flows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

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


TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

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
def client(db: Session, sms_sender: RecordingSmsSender) -> TestClient:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_sms_sender] = lambda: sms_sender

    with TestClient(app) as test_client:
        yield test_client

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
