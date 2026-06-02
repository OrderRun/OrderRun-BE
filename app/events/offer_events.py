from __future__ import annotations

from dataclasses import dataclass, field

from app.events.base import DomainEvent


@dataclass(frozen=True)
class OfferCreatedEvent(DomainEvent):
    offer_id: int
    proposal_id: int
    runner_id: str
    orderer_id: str
    proposal_title: str


@dataclass(frozen=True)
class OfferAcceptedEvent(DomainEvent):
    offer_id: int
    proposal_id: int
    accepted_runner_id: str
    rejected_runner_ids: tuple[str, ...]
    orderer_id: str
    proposal_title: str
