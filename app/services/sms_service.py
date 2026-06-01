"""SMS sender abstraction used by phone-auth flows."""

from __future__ import annotations

from typing import Protocol

from app.core.config import settings
from app.core.phone import normalize_phone


class SmsSender(Protocol):
    def send(self, phone: str, message: str) -> None:
        """Send an SMS message."""


class AwsSnsSmsSender:
    """SMS sender backed by AWS SNS."""

    def __init__(
        self,
        region_name: str,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        sender_id: str | None = None,
        sms_type: str = "Transactional",
        sns_client=None,
    ):
        self.region_name = region_name
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.sender_id = sender_id
        self.sms_type = sms_type
        self._sns_client = sns_client

    @staticmethod
    def _to_e164_kr(phone: str) -> str:
        normalized = normalize_phone(phone)
        if normalized.startswith("+"):
            return normalized
        if normalized.startswith("0"):
            return f"+82{normalized[1:]}"
        return normalized

    def _client(self):
        if self._sns_client is None:
            import boto3

            client_kwargs = {"region_name": self.region_name}
            if self.access_key_id and self.secret_access_key:
                client_kwargs["aws_access_key_id"] = self.access_key_id
                client_kwargs["aws_secret_access_key"] = self.secret_access_key
            self._sns_client = boto3.client("sns", **client_kwargs)
        return self._sns_client

    def send(self, phone: str, message: str) -> None:
        attributes = {
            "AWS.SNS.SMS.SMSType": {
                "DataType": "String",
                "StringValue": self.sms_type,
            }
        }
        if self.sender_id:
            attributes["AWS.SNS.SMS.SenderID"] = {
                "DataType": "String",
                "StringValue": self.sender_id,
            }

        self._client().publish(
            PhoneNumber=self._to_e164_kr(phone),
            Message=message,
            MessageAttributes=attributes,
        )


def get_sms_sender() -> SmsSender:
    return AwsSnsSmsSender(
        region_name=settings.aws_sns_region,
        access_key_id=settings.aws_sns_access_key_id,
        secret_access_key=settings.aws_sns_secret_access_key,
        sender_id=settings.aws_sns_sms_sender_id,
        sms_type=settings.aws_sns_sms_type,
    )
