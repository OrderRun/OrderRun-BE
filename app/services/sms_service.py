"""SMS sender abstraction used by phone-auth flows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Protocol


class SmsSender(Protocol):
    def send(self, phone: str, message: str) -> None:
        """Send an SMS message."""


@dataclass
class NoopSmsSender:
    """Default SMS sender used in local/dev environments."""

    sent_messages: List[dict] = field(default_factory=list)

    def send(self, phone: str, message: str) -> None:
        self.sent_messages.append({"phone": phone, "message": message})


def get_sms_sender() -> SmsSender:
    return NoopSmsSender()
