from __future__ import annotations

from dataclasses import dataclass

from app.events.base import DomainEvent


@dataclass(frozen=True)
class MeetingConfirmedByRunnerEvent(DomainEvent):
    """러너가 완료 처리했을 때 요청자에게 알림."""

    offer_id: int
    proposal_id: int
    runner_id: str
    orderer_id: str
    proposal_title: str


@dataclass(frozen=True)
class MeetingConfirmedByOrdererEvent(DomainEvent):
    """요청자가 완료 확인했을 때 러너에게 알림."""

    offer_id: int
    proposal_id: int
    orderer_id: str
    runner_id: str
    proposal_title: str


@dataclass(frozen=True)
class DisputeRaisedByOrdererEvent(DomainEvent):
    """요청자가 분쟁을 접수했을 때 러너에게 알림."""

    offer_id: int
    proposal_id: int
    orderer_id: str
    runner_id: str
    proposal_title: str


@dataclass(frozen=True)
class DisputeRaisedByRunnerEvent(DomainEvent):
    """러너가 분쟁을 접수했을 때 요청자에게 알림."""

    offer_id: int
    proposal_id: int
    runner_id: str
    orderer_id: str
    proposal_title: str
