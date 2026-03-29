"""Integration tests for user profile APIs."""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserStatus, OAuthProvider
from app.models.proposal import Proposal, ProposalStatus
from app.models.offer import Offer, OfferStatus
from app.core.security import create_access_token


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(
        email="testuser@example.com",
        nickname="Test User",
        phone_number="010-1234-5678",
        status=UserStatus.ACTIVE,
        oauth_provider=OAuthProvider.KAKAO,
        oauth_id="kakao_123",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Generate authentication headers."""
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_proposals(db: Session, test_user: User) -> list[Proposal]:
    """Create test proposals."""
    now = datetime.now(timezone.utc)
    proposals = [
        Proposal(
            orderer_id=test_user.id,
            title="Proposal 1",
            content="Content 1",
            deadline=now + timedelta(days=1),
            errand_fee=5000,
            status=ProposalStatus.POSTED,
            payment_status="CONFIRMED",
            payment_deadline=now + timedelta(hours=1),
        ),
        Proposal(
            orderer_id=test_user.id,
            title="Proposal 2",
            content="Content 2",
            deadline=now + timedelta(days=2),
            errand_fee=10000,
            status=ProposalStatus.MATCHED,
            payment_status="CONFIRMED",
            payment_deadline=now + timedelta(hours=1),
        ),
        Proposal(
            orderer_id=test_user.id,
            title="Proposal 3",
            content="Content 3",
            deadline=now + timedelta(days=3),
            errand_fee=7000,
            status=ProposalStatus.CANCELLED,
            payment_status="CONFIRMED",
            payment_deadline=now + timedelta(hours=1),
        ),
    ]

    for proposal in proposals:
        db.add(proposal)

    db.commit()

    for proposal in proposals:
        db.refresh(proposal)

    return proposals


@pytest.fixture
def test_offers(db: Session, test_user: User, test_proposals: list[Proposal]) -> list[Offer]:
    """Create test offers."""
    offers = [
        Offer(
            proposal_id=test_proposals[0].id,
            runner_id=test_user.id,
            estimated_time=30,
            message="I can do this",
            status=OfferStatus.WAITING,
        ),
        Offer(
            proposal_id=test_proposals[1].id,
            runner_id=test_user.id,
            estimated_time=45,
            message="Let me help",
            status=OfferStatus.ACCEPTED,
        ),
        Offer(
            proposal_id=test_proposals[2].id,
            runner_id=test_user.id,
            estimated_time=60,
            message="Available now",
            status=OfferStatus.REJECTED,
        ),
    ]

    for offer in offers:
        db.add(offer)

    db.commit()

    for offer in offers:
        db.refresh(offer)

    return offers


class TestUserProfileAPI:
    """Test user profile API endpoints."""

    def test_get_user_profile_with_both_roles(
        self, client: TestClient, auth_headers: dict, test_proposals: list[Proposal], test_offers: list[Offer]
    ):
        """Test getting user profile when user has both orderer and runner roles."""
        response = client.get("/api/v1/users/me/profile", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == "testuser@example.com"
        assert data["nickname"] == "Test User"
        assert data["phoneNumber"] == "010-1234-5678"
        assert data["status"] == "active"
        assert data["isAdmin"] is False
        assert data["oauthProvider"] == "kakao"

        # Check roles
        assert data["roles"]["isOrderer"] is True
        assert data["roles"]["isRunner"] is True

    def test_get_user_profile_orderer_only(
        self, client: TestClient, auth_headers: dict, test_proposals: list[Proposal]
    ):
        """Test getting user profile when user is only an orderer."""
        response = client.get("/api/v1/users/me/profile", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["roles"]["isOrderer"] is True
        assert data["roles"]["isRunner"] is False

    def test_get_user_profile_runner_only(
        self, client: TestClient, auth_headers: dict, test_offers: list[Offer]
    ):
        """Test getting user profile when user is only a runner."""
        response = client.get("/api/v1/users/me/profile", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["roles"]["isOrderer"] is False
        assert data["roles"]["isRunner"] is True

    def test_get_user_profile_no_activity(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting user profile when user has no activity."""
        response = client.get("/api/v1/users/me/profile", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["roles"]["isOrderer"] is False
        assert data["roles"]["isRunner"] is False

    def test_get_user_activity(
        self, client: TestClient, auth_headers: dict, test_proposals: list[Proposal], test_offers: list[Offer]
    ):
        """Test getting user activity statistics."""
        response = client.get("/api/v1/users/me/activity", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Check orderer activity
        orderer = data["ordererActivity"]
        assert orderer["totalProposals"] == 3
        assert orderer["activeProposals"] == 1  # POSTED
        assert orderer["completedProposals"] == 1  # MATCHED
        assert orderer["cancelledProposals"] == 1  # CANCELLED
        assert orderer["totalSpent"] == 10000  # Only matched proposal
        assert len(orderer["recentProposals"]) == 3

        # Check runner activity
        runner = data["runnerActivity"]
        assert runner["totalOffers"] == 3
        assert runner["waitingOffers"] == 1  # WAITING
        assert runner["acceptedOffers"] == 1  # ACCEPTED
        assert runner["rejectedOffers"] == 1  # REJECTED
        assert runner["acceptanceRate"] == 0.5  # 1 accepted / 2 responded
        assert runner["totalEarnings"] == 10000  # Errand fee from accepted offer
        assert len(runner["recentOffers"]) == 3

    def test_get_user_proposals(
        self, client: TestClient, auth_headers: dict, test_proposals: list[Proposal]
    ):
        """Test getting user's proposals."""
        response = client.get("/api/v1/users/me/proposals", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 3
        assert all(p["ordererId"] == test_proposals[0].orderer_id for p in data)

    def test_get_user_proposals_filtered_by_status(
        self, client: TestClient, auth_headers: dict, test_proposals: list[Proposal]
    ):
        """Test getting user's proposals filtered by status."""
        response = client.get(
            "/api/v1/users/me/proposals",
            params={"status": "MATCHED"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["status"] == "MATCHED"

    def test_get_user_proposals_pagination(
        self, client: TestClient, auth_headers: dict, test_proposals: list[Proposal]
    ):
        """Test getting user's proposals with pagination."""
        response = client.get(
            "/api/v1/users/me/proposals",
            params={"page": 1, "limit": 2},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2

    def test_get_user_offers(
        self, client: TestClient, auth_headers: dict, test_offers: list[Offer]
    ):
        """Test getting user's offers."""
        response = client.get("/api/v1/users/me/offers", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 3
        assert all(o["runnerId"] == test_offers[0].runner_id for o in data)

    def test_get_user_offers_filtered_by_status(
        self, client: TestClient, auth_headers: dict, test_offers: list[Offer]
    ):
        """Test getting user's offers filtered by status."""
        response = client.get(
            "/api/v1/users/me/offers",
            params={"status": "ACCEPTED"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["status"] == "ACCEPTED"

    def test_get_user_offers_pagination(
        self, client: TestClient, auth_headers: dict, test_offers: list[Offer]
    ):
        """Test getting user's offers with pagination."""
        response = client.get(
            "/api/v1/users/me/offers",
            params={"page": 1, "limit": 2},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2

    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication."""
        endpoints = [
            "/api/v1/users/me/profile",
            "/api/v1/users/me/activity",
            "/api/v1/users/me/proposals",
            "/api/v1/users/me/offers",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
