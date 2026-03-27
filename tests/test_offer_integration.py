"""Integration tests for Offer API."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.proposal import Proposal, ProposalStatus
from app.models.offer import Offer, OfferStatus
from app.models.user import User, UserRole, UserStatus, OAuthProvider


@pytest.fixture
def sample_customer(db: Session) -> User:
    """Create a sample customer user."""
    user = User(
        email="customer@example.com",
        nickname="Customer",
        role=UserRole.CUSTOMER,
        status=UserStatus.ACTIVE,
        oauth_provider=OAuthProvider.KAKAO,
        oauth_id="customer123",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_runner(db: Session) -> User:
    """Create a sample runner user."""
    user = User(
        email="runner@example.com",
        nickname="Runner",
        role=UserRole.RUNNER,
        status=UserStatus.ACTIVE,
        oauth_provider=OAuthProvider.KAKAO,
        oauth_id="runner123",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_runner2(db: Session) -> User:
    """Create another sample runner user."""
    user = User(
        email="runner2@example.com",
        nickname="Runner2",
        role=UserRole.RUNNER,
        status=UserStatus.ACTIVE,
        oauth_provider=OAuthProvider.KAKAO,
        oauth_id="runner456",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def posted_proposal(db: Session, sample_customer: User) -> Proposal:
    """Create a proposal in POSTED status."""
    proposal = Proposal(
        orderer_id=sample_customer.id,
        title="Test Proposal",
        content="Test content",
        deadline=datetime.utcnow() + timedelta(hours=2),
        errand_fee=10000,
        status=ProposalStatus.POSTED
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


@pytest.fixture
def offered_proposal(db: Session, sample_customer: User) -> Proposal:
    """Create a proposal in OFFERED status."""
    proposal = Proposal(
        orderer_id=sample_customer.id,
        title="Offered Proposal",
        content="Test content",
        deadline=datetime.utcnow() + timedelta(hours=2),
        errand_fee=10000,
        status=ProposalStatus.OFFERED
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


@pytest.fixture
def matched_proposal(db: Session, sample_customer: User) -> Proposal:
    """Create a proposal in MATCHED status."""
    proposal = Proposal(
        orderer_id=sample_customer.id,
        title="Matched Proposal",
        content="Test content",
        deadline=datetime.utcnow() + timedelta(hours=2),
        errand_fee=10000,
        status=ProposalStatus.MATCHED
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


class TestOfferCreation:
    """Test offer creation scenarios."""

    def test_create_offer_success(
        self,
        client: TestClient,
        db: Session,
        posted_proposal: Proposal,
        sample_runner: User
    ):
        """Test successful offer creation."""
        payload = {
            "proposal_id": posted_proposal.id,
            "runner_id": sample_runner.id,
            "estimated_time": 30,
            "message": "30분 안에 가능합니다."
        }

        response = client.post("/api/v1/offer", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "제안이 제출되었습니다."
        assert data["data"]["proposalId"] == posted_proposal.id
        assert data["data"]["runnerId"] == sample_runner.id
        assert data["data"]["estimatedTime"] == 30
        assert data["data"]["message"] == "30분 안에 가능합니다."
        assert data["data"]["status"] == "WAITING"
        assert "createdAt" in data["data"]

        # Verify database
        offer = db.query(Offer).filter(Offer.id == data["data"]["id"]).first()
        assert offer is not None
        assert offer.status == OfferStatus.WAITING

    def test_first_offer_changes_proposal_status(
        self,
        client: TestClient,
        db: Session,
        posted_proposal: Proposal,
        sample_runner: User
    ):
        """Test that first offer changes proposal status to OFFERED."""
        payload = {
            "proposal_id": posted_proposal.id,
            "runner_id": sample_runner.id,
            "estimated_time": 30,
            "message": "Test offer"
        }

        response = client.post("/api/v1/offer", json=payload)

        assert response.status_code == 201

        # Verify proposal status changed
        db.refresh(posted_proposal)
        assert posted_proposal.status == ProposalStatus.OFFERED

    def test_create_offer_without_message(
        self,
        client: TestClient,
        db: Session,
        posted_proposal: Proposal,
        sample_runner: User
    ):
        """Test creating offer without optional message."""
        payload = {
            "proposal_id": posted_proposal.id,
            "runner_id": sample_runner.id,
            "estimated_time": 25
        }

        response = client.post("/api/v1/offer", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["message"] is None


class TestOfferCreationValidation:
    """Test offer creation validation failures."""

    def test_create_offer_missing_proposal_id(
        self,
        client: TestClient,
        sample_runner: User
    ):
        """Test creating offer without proposal_id."""
        payload = {
            "runner_id": sample_runner.id,
            "estimated_time": 30
        }

        response = client.post("/api/v1/offer", json=payload)

        assert response.status_code == 400

    def test_create_offer_missing_runner_id(
        self,
        client: TestClient,
        posted_proposal: Proposal
    ):
        """Test creating offer without runner_id."""
        payload = {
            "proposal_id": posted_proposal.id,
            "estimated_time": 30
        }

        response = client.post("/api/v1/offer", json=payload)

        assert response.status_code == 400

    def test_create_offer_missing_estimated_time(
        self,
        client: TestClient,
        posted_proposal: Proposal,
        sample_runner: User
    ):
        """Test creating offer without estimated_time."""
        payload = {
            "proposal_id": posted_proposal.id,
            "runner_id": sample_runner.id
        }

        response = client.post("/api/v1/offer", json=payload)

        assert response.status_code == 400

    def test_create_offer_invalid_estimated_time(
        self,
        client: TestClient,
        posted_proposal: Proposal,
        sample_runner: User
    ):
        """Test creating offer with estimated_time < 1."""
        payload = {
            "proposal_id": posted_proposal.id,
            "runner_id": sample_runner.id,
            "estimated_time": 0
        }

        response = client.post("/api/v1/offer", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_create_offer_message_too_long(
        self,
        client: TestClient,
        posted_proposal: Proposal,
        sample_runner: User
    ):
        """Test creating offer with message > 500 characters."""
        payload = {
            "proposal_id": posted_proposal.id,
            "runner_id": sample_runner.id,
            "estimated_time": 30,
            "message": "a" * 501
        }

        response = client.post("/api/v1/offer", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"


class TestOfferCreationBusinessRules:
    """Test offer creation business rule violations."""

    def test_create_duplicate_offer(
        self,
        client: TestClient,
        db: Session,
        posted_proposal: Proposal,
        sample_runner: User
    ):
        """Test creating duplicate offer by same runner."""
        payload = {
            "proposal_id": posted_proposal.id,
            "runner_id": sample_runner.id,
            "estimated_time": 30,
            "message": "First offer"
        }

        # Create first offer
        response1 = client.post("/api/v1/offer", json=payload)
        assert response1.status_code == 201

        # Attempt to create second offer
        payload["message"] = "Second offer"
        response2 = client.post("/api/v1/offer", json=payload)

        assert response2.status_code == 409
        data = response2.json()
        assert data["success"] is False
        assert data["error"]["code"] == "DUPLICATE_OFFER"
        assert "이미 해당 요청에 제안을 제출했습니다" in data["error"]["message"]

    def test_create_offer_proposal_not_open(
        self,
        client: TestClient,
        matched_proposal: Proposal,
        sample_runner: User
    ):
        """Test creating offer when proposal is not POSTED or OFFERED."""
        payload = {
            "proposal_id": matched_proposal.id,
            "runner_id": sample_runner.id,
            "estimated_time": 30
        }

        response = client.post("/api/v1/offer", json=payload)

        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PROPOSAL_NOT_OPEN"
        assert "제안을 받을 수 없는 요청 상태입니다" in data["error"]["message"]

    def test_create_offer_proposal_not_found(
        self,
        client: TestClient,
        sample_runner: User
    ):
        """Test creating offer for non-existent proposal."""
        payload = {
            "proposal_id": 99999,
            "runner_id": sample_runner.id,
            "estimated_time": 30
        }

        response = client.post("/api/v1/offer", json=payload)

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PROPOSAL_NOT_FOUND"


class TestOfferList:
    """Test offer list retrieval scenarios."""

    def test_get_offers_success(
        self,
        client: TestClient,
        db: Session,
        posted_proposal: Proposal,
        sample_runner: User,
        sample_runner2: User
    ):
        """Test successful offer list retrieval."""
        # Create two offers
        offer1 = Offer(
            proposal_id=posted_proposal.id,
            runner_id=sample_runner.id,
            estimated_time=30,
            message="First offer"
        )
        offer2 = Offer(
            proposal_id=posted_proposal.id,
            runner_id=sample_runner2.id,
            estimated_time=25,
            message="Second offer"
        )
        db.add(offer1)
        db.add(offer2)
        db.commit()

        response = client.get(f"/api/v1/offer?proposalId={posted_proposal.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2

        # Verify newest first (descending order by created_at)
        # Since both offers are created at the same time, check by ID (latest ID first)
        offer_ids = [item["id"] for item in data["data"]]
        assert offer_ids[0] > offer_ids[1], "Offers should be sorted by created_at desc (and ID desc if same time)"

    def test_get_offers_empty_list(
        self,
        client: TestClient,
        posted_proposal: Proposal
    ):
        """Test retrieving empty offer list."""
        response = client.get(f"/api/v1/offer?proposalId={posted_proposal.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_get_offers_proposal_not_found(
        self,
        client: TestClient
    ):
        """Test retrieving offers for non-existent proposal."""
        response = client.get("/api/v1/offer?proposalId=99999")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PROPOSAL_NOT_FOUND"

    def test_get_offers_filters_by_proposal(
        self,
        client: TestClient,
        db: Session,
        posted_proposal: Proposal,
        sample_customer: User,
        sample_runner: User
    ):
        """Test that offers are filtered by proposal_id."""
        # Create another proposal
        another_proposal = Proposal(
            orderer_id=sample_customer.id,
            title="Another Proposal",
            content="Test content",
            deadline=datetime.utcnow() + timedelta(hours=2),
            errand_fee=10000,
            status=ProposalStatus.POSTED
        )
        db.add(another_proposal)
        db.commit()
        db.refresh(another_proposal)

        # Create offers for both proposals
        offer1 = Offer(
            proposal_id=posted_proposal.id,
            runner_id=sample_runner.id,
            estimated_time=30
        )
        offer2 = Offer(
            proposal_id=another_proposal.id,
            runner_id=sample_runner.id,
            estimated_time=25
        )
        db.add(offer1)
        db.add(offer2)
        db.commit()

        # Query first proposal
        response = client.get(f"/api/v1/offer?proposalId={posted_proposal.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["proposalId"] == posted_proposal.id
