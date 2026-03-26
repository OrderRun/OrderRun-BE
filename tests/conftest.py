"""Pytest configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User

# Test database URL (use MySQL test database)
TEST_DATABASE_URL = "mysql+pymysql://orderrun_user:orderrun_pass@localhost:3306/orderrun_test"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True
)

# Create test session
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database for each test.
    """
    # Create tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db: Session) -> TestClient:
    """
    Create a test client with database dependency override.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db: Session) -> User:
    """
    Create a sample user for testing.
    """
    from app.models.user import User, UserRole, UserStatus, OAuthProvider

    user = User(
        email="test@example.com",
        nickname="Test User",
        role=UserRole.CUSTOMER,
        status=UserStatus.ACTIVE,
        oauth_provider=OAuthProvider.KAKAO,
        oauth_id="123456789",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def auth_headers(sample_user: User) -> dict:
    """
    Create authentication headers with JWT token.
    """
    from app.core.security import create_access_token

    access_token = create_access_token({"sub": str(sample_user.id)})

    return {"Authorization": f"Bearer {access_token}"}
