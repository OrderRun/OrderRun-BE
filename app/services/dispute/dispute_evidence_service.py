"""Dispute evidence queries."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import AppError, api_error
from app.models.dispute_evidence import DisputeEvidence
from app.models.offer import Offer
from app.models.proposal import Proposal
from app.schemas.dispute_evidence import DisputeEvidenceResponse


class DisputeEvidenceService:
    @staticmethod
    def _ensure_participant(db: Session, evidence: DisputeEvidence, viewer_id: str) -> None:
        row = (
            db.query(Proposal.orderer_id, Offer.runner_id)
            .join(Offer, Offer.id == evidence.offer_id)
            .filter(Proposal.id == evidence.proposal_id)
            .one_or_none()
        )
        if row is None:
            raise api_error(AppError.DISPUTE_EVIDENCE_NOT_FOUND)
        orderer_id, runner_id = row
        if viewer_id not in {orderer_id, runner_id}:
            raise api_error(AppError.FORBIDDEN)

    @staticmethod
    def get_by_proposal_id(db: Session, proposal_id: int, viewer_id: str) -> DisputeEvidenceResponse:
        evidence = (
            db.query(DisputeEvidence)
            .filter(DisputeEvidence.proposal_id == proposal_id)
            .order_by(DisputeEvidence.created_at.desc(), DisputeEvidence.id.desc())
            .first()
        )
        if evidence is None:
            raise api_error(AppError.DISPUTE_EVIDENCE_NOT_FOUND, f"proposalId: {proposal_id}")
        DisputeEvidenceService._ensure_participant(db, evidence, viewer_id)
        return DisputeEvidenceResponse.model_validate(evidence)

    @staticmethod
    def get_by_offer_id(db: Session, offer_id: int, viewer_id: str) -> DisputeEvidenceResponse:
        evidence = (
            db.query(DisputeEvidence)
            .filter(DisputeEvidence.offer_id == offer_id)
            .order_by(DisputeEvidence.created_at.desc(), DisputeEvidence.id.desc())
            .first()
        )
        if evidence is None:
            raise api_error(AppError.DISPUTE_EVIDENCE_NOT_FOUND, f"offerId: {offer_id}")
        DisputeEvidenceService._ensure_participant(db, evidence, viewer_id)
        return DisputeEvidenceResponse.model_validate(evidence)
