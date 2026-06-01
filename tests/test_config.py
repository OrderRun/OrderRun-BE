from __future__ import annotations

from app.core.config import Settings


def test_settings_load_without_oauth_or_email_values():
    settings = Settings(
        secret_key="test-secret",
        db_username="test-user",
        db_password="test-password",
        db_name="test-db",
        jwt_secret="test-jwt",
    )

    assert settings.secret_key == "test-secret"
    assert settings.jwt_secret == "test-jwt"


def test_settings_load_aws_sns_values():
    settings = Settings(
        secret_key="test-secret",
        db_username="test-user",
        db_password="test-password",
        db_name="test-db",
        jwt_secret="test-jwt",
        aws_sns_region="us-east-1",
        aws_sns_access_key_id="access-key",
        aws_sns_secret_access_key="secret-key",
        aws_sns_sms_sender_id="OrderRun",
        aws_sns_sms_type="Promotional",
    )

    assert settings.aws_sns_region == "us-east-1"
    assert settings.aws_sns_access_key_id == "access-key"
    assert settings.aws_sns_secret_access_key == "secret-key"
    assert settings.aws_sns_sms_sender_id == "OrderRun"
    assert settings.aws_sns_sms_type == "Promotional"
