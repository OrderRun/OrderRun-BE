"""Integration tests for Mission API."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.models.proposal import Proposal, ProposalStatus
from app.models.offer import Offer, OfferStatus
from app.models.mission import Mission, MissionStatus
from app.models.user import User, UserStatus, OAuthProvider


@pytest.fixture
def sample_orderer(db: Session) -> User:
    """Create a sample orderer user."""
    user = User(
        email="orderer@example.com",
        nickname="Orderer",
        status=UserStatus.ACTIVE,
        is_admin=False,
        oauth_provider=OAuthProvider.KAKAO,
        oauth_id="orderer123",
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
        status=UserStatus.ACTIVE,
        is_admin=False,
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
        status=UserStatus.ACTIVE,
        is_admin=False,
        oauth_provider=OAuthProvider.KAKAO,
        oauth_id="runner456",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def offered_proposal(db: Session, sample_orderer: User) -> Proposal:
    """Create a proposal in OFFERED status with payment confirmed."""
    proposal = Proposal(
        orderer_id=sample_orderer.id,
        title="Test Proposal",
        content="Test content",
        deadline=datetime.now(timezone.utc) + timedelta(hours=2),
        errand_fee=10000,
        status=ProposalStatus.OFFERED,
        payment_status="CONFIRMED",
        payment_deadline=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


@pytest.fixture
def waiting_offer(db: Session, offered_proposal: Proposal, sample_runner: User) -> Offer:
    """Create an offer in WAITING status."""
    offer = Offer(
        proposal_id=offered_proposal.id,
        runner_id=sample_runner.id,
        estimated_time=30,
        message="I can do it in 30 minutes",
        status=OfferStatus.WAITING
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


class TestAcceptOffer:
    """Test accept offer and create mission scenarios."""

    def test_accept_offer_success(
        self,
        client: TestClient,
        db: Session,
        offered_proposal: Proposal,
        waiting_offer: Offer,
        sample_orderer: User,
        sample_runner: User
    ):
        """Test successful offer acceptance and mission creation."""
        # Create auth headers for the orderer
        from app.core.security import create_access_token
        access_token = create_access_token({"sub": str(sample_orderer.id)})
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.post(
            f"/api/v1/offer/{waiting_offer.id}/accept",
            headers=headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "제안이 수락되어 미션이 생성되었습니다."

        # Verify mission data
        mission_data = data["data"]
        assert mission_data["proposalId"] == offered_proposal.id
        assert mission_data["offerId"] == waiting_offer.id
        assert mission_data["ordererId"] == sample_orderer.id
        assert mission_data["runnerId"] == sample_runner.id
        assert mission_data["contractAmount"] == offered_proposal.errand_fee
        assert mission_data["status"] == "CREATED"
        assert "createdAt" in mission_data

        # Verify database changes
        db.refresh(waiting_offer)
        assert waiting_offer.status == OfferStatus.ACCEPTED

        db.refresh(offered_proposal)
        assert offered_proposal.status == ProposalStatus.MATCHED

        # Verify mission created in database
        mission = db.query(Mission).filter(Mission.id == mission_data["id"]).first()
        assert mission is not None
        assert mission.status == MissionStatus.CREATED

    def test_accept_offer_rejects_other_offers(
        self,
        client: TestClient,
        db: Session,
        offered_proposal: Proposal,
        waiting_offer: Offer,
        sample_orderer: User,
        sample_runner2: User
    ):
        """Test that accepting one offer rejects other waiting offers."""
        # Create another waiting offer
        another_offer = Offer(
            proposal_id=offered_proposal.id,
            runner_id=sample_runner2.id,
            estimated_time=25,
            message="I can do it faster",
            status=OfferStatus.WAITING
        )
        db.add(another_offer)
        db.commit()
        db.refresh(another_offer)

        # Accept the first offer
        from app.core.security import create_access_token
        access_token = create_access_token({"sub": str(sample_orderer.id)})
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.post(
            f"/api/v1/offer/{waiting_offer.id}/accept",
            headers=headers
        )

        assert response.status_code == 201

        # Verify the other offer was rejected
        db.refresh(another_offer)
        assert another_offer.status == OfferStatus.REJECTED

    def test_accept_offer_unauthorized(
        self,
        client: TestClient,
        waiting_offer: Offer
    ):
        """Test accepting offer without authentication."""
        response = client.post(f"/api/v1/offer/{waiting_offer.id}/accept")

        assert response.status_code == 401

    def test_accept_offer_forbidden_not_orderer(
        self,
        client: TestClient,
        db: Session,
        sample_orderer: User,
        offered_proposal: Proposal,
        waiting_offer: Offer,
        sample_runner: User,
        sample_runner2: User
    ):
        """Test accepting offer by non-orderer user."""
        # Create auth headers for another runner (not the orderer)
        from app.core.security import create_access_token
        access_token = create_access_token({"sub": str(sample_runner2.id)})
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.post(
            f"/api/v1/offer/{waiting_offer.id}/accept",
            headers=headers
        )

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FORBIDDEN"
        assert "본인의 요청에 대한 제안만 수락할 수 있습니다" in data["error"]["message"]

    def test_accept_offer_not_found(
        self,
        client: TestClient,
        db: Session,
        sample_orderer: User
    ):
        """Test accepting non-existent offer."""
        from app.core.security import create_access_token
        access_token = create_access_token({"sub": str(sample_orderer.id)})
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.post(
            "/api/v1/offer/99999/accept",
            headers=headers
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "OFFER_NOT_FOUND"

    def test_accept_already_accepted_offer(
        self,
        client: TestClient,
        db: Session,
        offered_proposal: Proposal,
        sample_orderer: User,
        sample_runner: User
    ):
        """Test accepting an already accepted offer."""
        # Create an already accepted offer
        accepted_offer = Offer(
            proposal_id=offered_proposal.id,
            runner_id=sample_runner.id,
            estimated_time=30,
            message="Test",
            status=OfferStatus.ACCEPTED
        )
        db.add(accepted_offer)
        db.commit()
        db.refresh(accepted_offer)

        from app.core.security import create_access_token
        access_token = create_access_token({"sub": str(sample_orderer.id)})
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.post(
            f"/api/v1/offer/{accepted_offer.id}/accept",
            headers=headers
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_OFFER_STATUS"
        assert "이미 처리된 제안입니다" in data["error"]["message"]

    def test_accept_offer_proposal_already_matched(
        self,
        client: TestClient,
        db: Session,
        sample_orderer: User,
        sample_runner: User
    ):
        """Test accepting offer when proposal is already matched."""
        # Create a matched proposal
        matched_proposal = Proposal(
            orderer_id=sample_orderer.id,
            title="Matched Proposal",
            content="Test content",
            deadline=datetime.now(timezone.utc) + timedelta(hours=2),
            errand_fee=10000,
            status=ProposalStatus.MATCHED,
            payment_status="CONFIRMED",
            payment_deadline=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        db.add(matched_proposal)
        db.commit()
        db.refresh(matched_proposal)

        # Create a waiting offer for the matched proposal
        offer = Offer(
            proposal_id=matched_proposal.id,
            runner_id=sample_runner.id,
            estimated_time=30,
            message="Test",
            status=OfferStatus.WAITING
        )
        db.add(offer)
        db.commit()
        db.refresh(offer)

        from app.core.security import create_access_token
        access_token = create_access_token({"sub": str(sample_orderer.id)})
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.post(
            f"/api/v1/offer/{offer.id}/accept",
            headers=headers
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_PROPOSAL_STATUS"
        assert "제안을 받을 수 없는 요청 상태입니다" in data["error"]["message"]
