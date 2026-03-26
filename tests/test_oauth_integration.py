"""Integration tests for OAuth authentication with mocked providers."""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, OAuthProvider
from app.schemas.user import OAuthUserInfo


class TestKakaoOAuthIntegration:
    """Integration tests for Kakao OAuth flow."""

    @pytest.fixture
    def mock_kakao_responses(self):
        """Mock Kakao API responses."""
        return {
            "access_token": "mock_kakao_access_token",
            "user_info": {
                "id": 9876543210,
                "kakao_account": {
                    "email": "kakao_user@example.com",
                    "profile": {
                        "nickname": "카카오유저"
                    }
                }
            }
        }

    def test_kakao_login_returns_authorization_url(self, client: TestClient):
        """Test that /auth/kakao returns authorization URL."""
        response = client.get("/api/v1/auth/kakao")

        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "kauth.kakao.com/oauth/authorize" in data["authorization_url"]
        assert "client_id" in data["authorization_url"]

    @patch("app.services.oauth.kakao.httpx.AsyncClient")
    def test_kakao_callback_creates_new_user(
        self,
        mock_async_client,
        client: TestClient,
        db: Session,
        mock_kakao_responses
    ):
        """Test Kakao callback creates a new user and returns tokens."""
        # Mock token exchange
        mock_token_response = AsyncMock()
        mock_token_response.status_code = 200
        mock_token_response.json = lambda: {"access_token": mock_kakao_responses["access_token"]}

        # Mock user info retrieval
        mock_user_info_response = AsyncMock()
        mock_user_info_response.status_code = 200
        mock_user_info_response.json = lambda: mock_kakao_responses["user_info"]

        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_token_response)
        mock_client_instance.get = AsyncMock(return_value=mock_user_info_response)
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Make request
        response = client.get("/api/v1/auth/kakao/callback?code=test_auth_code")

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

        # Verify user was created
        user = db.query(User).filter(User.email == "kakao_user@example.com").first()
        assert user is not None
        assert user.oauth_provider == OAuthProvider.KAKAO
        assert user.oauth_id == "9876543210"
        assert user.nickname == "카카오유저"

    @patch("app.services.oauth.kakao.httpx.AsyncClient")
    def test_kakao_callback_updates_existing_user(
        self,
        mock_async_client,
        client: TestClient,
        db: Session,
        mock_kakao_responses
    ):
        """Test Kakao callback updates existing user instead of creating duplicate."""
        # Create existing user
        from app.models.user import UserRole, UserStatus, OAuthProvider

        existing_user = User(
            email="old_email@example.com",
            nickname="Old Nickname",
            oauth_provider=OAuthProvider.KAKAO,
            oauth_id="9876543210",  # Same OAuth ID
            role=UserRole.CUSTOMER,
            status=UserStatus.ACTIVE,
        )
        db.add(existing_user)
        db.commit()
        existing_user_id = existing_user.id

        # Mock responses
        mock_token_response = AsyncMock()
        mock_token_response.status_code = 200
        mock_token_response.json = lambda: {"access_token": mock_kakao_responses["access_token"]}

        mock_user_info_response = AsyncMock()
        mock_user_info_response.status_code = 200
        mock_user_info_response.json = lambda: mock_kakao_responses["user_info"]

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_token_response)
        mock_client_instance.get = AsyncMock(return_value=mock_user_info_response)
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Make request
        response = client.get("/api/v1/auth/kakao/callback?code=test_auth_code")

        # Assertions
        assert response.status_code == 200

        # Verify user was updated, not created
        users = db.query(User).all()
        assert len(users) == 1  # Still only one user

        updated_user = db.query(User).filter(User.id == existing_user_id).first()
        assert updated_user.email == "kakao_user@example.com"  # Updated
        assert updated_user.nickname == "카카오유저"  # Updated
        assert updated_user.oauth_id == "9876543210"  # Same


class TestAppleOAuthIntegration:
    """Integration tests for Apple OAuth flow."""

    @pytest.fixture
    def mock_apple_id_token(self):
        """Mock Apple ID token (JWT)."""
        import time
        from jose import jwt
        from app.core.config import settings

        payload = {
            "sub": "001234.abcdef1234567890.1234",
            "email": "apple_user@privaterelay.appleid.com",
            "email_verified": True,
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }

        return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

    def test_apple_login_returns_authorization_url(self, client: TestClient):
        """Test that /auth/apple returns authorization URL."""
        response = client.get("/api/v1/auth/apple")

        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "appleid.apple.com/auth/authorize" in data["authorization_url"]
        assert "client_id" in data["authorization_url"]

    @patch("app.services.oauth.apple.httpx.AsyncClient")
    def test_apple_callback_creates_new_user(
        self,
        mock_async_client,
        client: TestClient,
        db: Session,
        mock_apple_id_token
    ):
        """Test Apple callback creates a new user and returns tokens."""
        # Mock token exchange
        mock_token_response = AsyncMock()
        mock_token_response.status_code = 200
        mock_token_response.json = lambda: {"id_token": mock_apple_id_token}

        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_token_response)
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Make request
        response = client.post("/api/v1/auth/apple/callback?code=test_auth_code")

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Verify user was created
        from app.models.user import OAuthProvider

        user = db.query(User).filter(
            User.oauth_provider == OAuthProvider.APPLE
        ).first()
        assert user is not None
        assert user.oauth_id == "001234.abcdef1234567890.1234"
        assert user.email == "apple_user@privaterelay.appleid.com"


class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication."""

    def test_get_me_with_valid_token(self, client: TestClient, sample_user: User, auth_headers: dict):
        """Test /auth/me returns current user with valid token."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == sample_user.id
        assert data["email"] == sample_user.email
        assert data["nickname"] == sample_user.nickname
        assert data["role"] == sample_user.role.value
        assert data["status"] == sample_user.status.value

    def test_get_me_without_token_fails(self, client: TestClient):
        """Test /auth/me fails without token."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401  # Unauthorized (HTTPBearer returns 401)

    def test_get_me_with_invalid_token_fails(self, client: TestClient):
        """Test /auth/me fails with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 401  # Unauthorized

    def test_refresh_token_generates_new_tokens(
        self,
        client: TestClient,
        sample_user: User
    ):
        """Test /auth/refresh generates new tokens."""
        from app.core.security import create_refresh_token

        # Create refresh token
        refresh_token = create_refresh_token({"sub": str(sample_user.id)})

        # Request new tokens
        response = client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


class TestHealthAndRoot:
    """Test health check and root endpoints."""

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns welcome message."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
