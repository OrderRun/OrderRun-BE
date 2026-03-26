"""Integration tests for Proposal API."""
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


class TestProposalList:
    """Test GET /api/v1/proposal - List all proposals."""

    def test_list_proposals_empty(self, client: TestClient, db: Session):
        """Test listing proposals when database is empty."""
        response = client.get("/api/v1/proposal")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_list_proposals_with_data(self, client: TestClient, db: Session, sample_user: User):
        """Test listing proposals with existing data."""
        from app.models.proposal import Proposal, ProposalStatus

        # Create sample proposals
        proposal1 = Proposal(
            orderer_id=sample_user.id,
            title="커피 배달 부탁드립니다",
            content="스타벅스 아메리카노 2잔",
            deadline=datetime.now(timezone.utc) + timedelta(hours=5),
            errand_fee=5000,
            status=ProposalStatus.POSTED,
        )
        proposal2 = Proposal(
            orderer_id=sample_user.id,
            title="서류 전달 부탁드립니다",
            content="강남역 1번 출구에서 2번 출구로",
            deadline=datetime.now(timezone.utc) + timedelta(hours=3),
            errand_fee=3000,
            status=ProposalStatus.POSTED,
        )
        db.add(proposal1)
        db.add(proposal2)
        db.commit()

        response = client.get("/api/v1/proposal")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2

        # Check first proposal
        first = data["data"][0]
        assert "id" in first
        assert "ordererId" in first
        assert "title" in first
        assert "content" in first
        assert "deadline" in first
        assert "errandFee" in first
        assert "status" in first
        assert "createdAt" in first
        assert "updatedAt" in first


class TestProposalDetail:
    """Test GET /api/v1/proposal/{id} - Get proposal detail."""

    def test_get_proposal_detail_success(self, client: TestClient, db: Session, sample_user: User):
        """Test getting proposal detail successfully."""
        from app.models.proposal import Proposal, ProposalStatus

        # Create sample proposal
        deadline = datetime.now(timezone.utc) + timedelta(hours=5)
        proposal = Proposal(
            orderer_id=sample_user.id,
            title="커피 배달 부탁드립니다",
            content="스타벅스 아메리카노 아이스 2잔 부탁드립니다. 건물 입구에서 전달해주세요.",
            deadline=deadline,
            errand_fee=5000,
            status=ProposalStatus.POSTED,
        )
        db.add(proposal)
        db.commit()
        db.refresh(proposal)

        response = client.get(f"/api/v1/proposal/{proposal.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        proposal_data = data["data"]
        assert proposal_data["id"] == proposal.id
        assert proposal_data["ordererId"] == sample_user.id
        assert proposal_data["title"] == "커피 배달 부탁드립니다"
        assert proposal_data["content"] == "스타벅스 아메리카노 아이스 2잔 부탁드립니다. 건물 입구에서 전달해주세요."
        assert proposal_data["errandFee"] == 5000
        assert proposal_data["status"] == "POSTED"

    def test_get_proposal_not_found(self, client: TestClient, db: Session):
        """Test getting non-existent proposal returns 404."""
        response = client.get("/api/v1/proposal/9999")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PROPOSAL_NOT_FOUND"
        assert "timestamp" in data


class TestProposalCreate:
    """Test POST /api/v1/proposal - Create new proposal."""

    def test_create_proposal_success(self, client: TestClient, db: Session, sample_user: User, auth_headers: dict):
        """Test creating proposal successfully."""
        deadline = datetime.now(timezone.utc) + timedelta(hours=5)

        proposal_data = {
            "title": "강남역에서 커피 배달",
            "content": "스타벅스 아메리카노 아이스 2잔 부탁드립니다.",
            "deadline": deadline.isoformat(),
            "errandFee": 5000,
        }

        response = client.post("/api/v1/proposal", json=proposal_data, headers=auth_headers)

        if response.status_code != 201:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True

        created = data["data"]
        assert "id" in created
        assert created["ordererId"] == sample_user.id
        assert created["title"] == "강남역에서 커피 배달"
        assert created["content"] == "스타벅스 아메리카노 아이스 2잔 부탁드립니다."
        assert created["errandFee"] == 5000
        assert created["status"] == "POSTED"
        assert "createdAt" in created
        assert "updatedAt" in created

        # Verify saved in DB
        from app.models.proposal import Proposal
        db_proposal = db.query(Proposal).filter(Proposal.id == created["id"]).first()
        assert db_proposal is not None
        assert db_proposal.title == "강남역에서 커피 배달"
        assert db_proposal.status.value == "POSTED"

    def test_create_proposal_with_zero_fee(self, client: TestClient, db: Session, auth_headers: dict):
        """Test creating proposal with zero errand fee (boundary value)."""
        deadline = datetime.now(timezone.utc) + timedelta(hours=5)

        proposal_data = {
            "title": "무료 심부름",
            "content": "재능기부로 도와주세요.",
            "deadline": deadline.isoformat(),
            "errandFee": 0,
        }

        response = client.post("/api/v1/proposal", json=proposal_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["errandFee"] == 0

    def test_create_proposal_title_too_long(self, client: TestClient, auth_headers: dict):
        """Test creating proposal with title exceeding 50 characters."""
        deadline = datetime.now(timezone.utc) + timedelta(hours=5)

        proposal_data = {
            "title": "가" * 51,  # 51 characters
            "content": "내용입니다.",
            "deadline": deadline.isoformat(),
            "errandFee": 5000,
        }

        response = client.post("/api/v1/proposal", json=proposal_data, headers=auth_headers)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "title" in data["error"]["details"].lower()

    def test_create_proposal_title_empty(self, client: TestClient, auth_headers: dict):
        """Test creating proposal with empty title."""
        deadline = datetime.now(timezone.utc) + timedelta(hours=5)

        proposal_data = {
            "title": "",
            "content": "내용입니다.",
            "deadline": deadline.isoformat(),
            "errandFee": 5000,
        }

        response = client.post("/api/v1/proposal", json=proposal_data, headers=auth_headers)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_create_proposal_content_too_long(self, client: TestClient, auth_headers: dict):
        """Test creating proposal with content exceeding 500 characters."""
        deadline = datetime.now(timezone.utc) + timedelta(hours=5)

        proposal_data = {
            "title": "제목",
            "content": "가" * 501,  # 501 characters
            "deadline": deadline.isoformat(),
            "errandFee": 5000,
        }

        response = client.post("/api/v1/proposal", json=proposal_data, headers=auth_headers)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "content" in data["error"]["details"].lower()

    def test_create_proposal_content_empty(self, client: TestClient, auth_headers: dict):
        """Test creating proposal with empty content."""
        deadline = datetime.now(timezone.utc) + timedelta(hours=5)

        proposal_data = {
            "title": "제목",
            "content": "",
            "deadline": deadline.isoformat(),
            "errandFee": 5000,
        }

        response = client.post("/api/v1/proposal", json=proposal_data, headers=auth_headers)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_create_proposal_deadline_past(self, client: TestClient, auth_headers: dict):
        """Test creating proposal with deadline in the past."""
        past_deadline = datetime.now(timezone.utc) - timedelta(hours=1)

        proposal_data = {
            "title": "과거 데드라인",
            "content": "과거 시각으로 설정",
            "deadline": past_deadline.isoformat(),
            "errandFee": 5000,
        }

        response = client.post("/api/v1/proposal", json=proposal_data, headers=auth_headers)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "deadline" in data["error"]["details"].lower()

    def test_create_proposal_negative_fee(self, client: TestClient, auth_headers: dict):
        """Test creating proposal with negative errand fee."""
        deadline = datetime.now(timezone.utc) + timedelta(hours=5)

        proposal_data = {
            "title": "음수 금액",
            "content": "음수 금액 테스트",
            "deadline": deadline.isoformat(),
            "errandFee": -1000,
        }

        response = client.post("/api/v1/proposal", json=proposal_data, headers=auth_headers)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "errandfee" in data["error"]["details"].lower()

    def test_create_proposal_without_auth(self, client: TestClient):
        """Test creating proposal without authentication."""
        deadline = datetime.now(timezone.utc) + timedelta(hours=5)

        proposal_data = {
            "title": "인증 없음",
            "content": "인증 없이 생성 시도",
            "deadline": deadline.isoformat(),
            "errandFee": 5000,
        }

        response = client.post("/api/v1/proposal", json=proposal_data)

        assert response.status_code == 401

    def test_create_proposal_with_invalid_token(self, client: TestClient):
        """Test creating proposal with invalid token."""
        deadline = datetime.now(timezone.utc) + timedelta(hours=5)

        proposal_data = {
            "title": "잘못된 토큰",
            "content": "잘못된 토큰으로 생성 시도",
            "deadline": deadline.isoformat(),
            "errandFee": 5000,
        }

        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.post("/api/v1/proposal", json=proposal_data, headers=headers)

        assert response.status_code == 401


class TestProposalTimestamps:
    """Test timestamp behavior."""

    def test_created_at_and_updated_at_set_on_creation(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test that createdAt and updatedAt are set on creation."""
        deadline = datetime.now(timezone.utc) + timedelta(hours=5)
        before_create = datetime.now(timezone.utc)

        proposal_data = {
            "title": "타임스탬프 테스트",
            "content": "생성 시각 확인",
            "deadline": deadline.isoformat(),
            "errandFee": 5000,
        }

        response = client.post("/api/v1/proposal", json=proposal_data, headers=auth_headers)
        after_create = datetime.now(timezone.utc)

        assert response.status_code == 201
        data = response.json()

        created_at_str = data["data"]["createdAt"]
        updated_at_str = data["data"]["updatedAt"]

        # Verify timestamps are present and in ISO format
        assert created_at_str is not None
        assert updated_at_str is not None

        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))

        # createdAt should equal updatedAt on creation (within 1 second)
        time_diff = abs((created_at - updated_at).total_seconds())
        assert time_diff < 1
