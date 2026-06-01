from __future__ import annotations

from app.services.sms_service import AwsSnsSmsSender


class FakeSnsClient:
    def __init__(self):
        self.published = []

    def publish(self, **kwargs):
        self.published.append(kwargs)
        return {"MessageId": "message-1"}


def test_aws_sns_sms_sender_formats_korean_phone_number():
    assert AwsSnsSmsSender._to_e164_kr("01012345678") == "+821012345678"
    assert AwsSnsSmsSender._to_e164_kr("010-1234-5678") == "+821012345678"
    assert AwsSnsSmsSender._to_e164_kr("+821012345678") == "+821012345678"


def test_aws_sns_sms_sender_publishes_with_sms_attributes():
    sns_client = FakeSnsClient()
    sender = AwsSnsSmsSender(
        region_name="ap-northeast-2",
        sender_id="Kkobongdan",
        sms_type="Transactional",
        sns_client=sns_client,
    )

    sender.send("010-1234-5678", "인증번호는 123456 입니다.")

    assert sns_client.published == [
        {
            "PhoneNumber": "+821012345678",
            "Message": "인증번호는 123456 입니다.",
            "MessageAttributes": {
                "AWS.SNS.SMS.SMSType": {
                    "DataType": "String",
                    "StringValue": "Transactional",
                },
                "AWS.SNS.SMS.SenderID": {
                    "DataType": "String",
                    "StringValue": "Kkobongdan",
                },
            },
        }
    ]


def test_aws_sns_sms_sender_propagates_provider_errors():
    class FailingSnsClient:
        def publish(self, **kwargs):
            raise RuntimeError("sns failed")

    sender = AwsSnsSmsSender(
        region_name="ap-northeast-2",
        sns_client=FailingSnsClient(),
    )

    try:
        sender.send("01012345678", "message")
    except RuntimeError as exc:
        assert str(exc) == "sns failed"
    else:
        raise AssertionError("Expected provider error")
