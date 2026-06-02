from __future__ import annotations

from dataclasses import dataclass

from app.events.base import DomainEvent


@dataclass(frozen=True)
class MeetingConfirmedByRunnerEvent(DomainEvent):
    """러너가 만남 확인(전달 완료)했을 때 — 요청자에게 알림."""
    mission_id: int
    proposal_id: int
    runner_id: str
    orderer_id: str
    proposal_title: str


@dataclass(frozen=True)
class MeetingConfirmedByOrdererEvent(DomainEvent):
    """요청자가 만남 확인(수령 확인)했을 때 — 러너에게 알림 + 양측 완료 알림."""
    mission_id: int
    proposal_id: int
    orderer_id: str
    runner_id: str
    proposal_title: str
