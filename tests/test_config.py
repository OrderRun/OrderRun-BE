from __future__ import annotations

import logging

from app.core.config import Settings
from app.core.logging import setup_logging
from app.core.logging import settings as global_settings


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


def test_settings_logging_defaults_are_console_only():
    settings = Settings(
        secret_key="test-secret",
        db_username="test-user",
        db_password="test-password",
        db_name="test-db",
        jwt_secret="test-jwt",
    )

    assert settings.log_level == "INFO"
    assert settings.log_dir == "/app/logs"
    assert settings.log_file_enabled is False
    assert settings.log_retention_days == 14


def test_setup_logging_writes_daily_file_when_enabled(tmp_path, monkeypatch):
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level

    monkeypatch.setattr(global_settings, "log_level", "INFO")
    monkeypatch.setattr(global_settings, "log_dir", str(tmp_path))
    monkeypatch.setattr(global_settings, "log_file_enabled", True)
    monkeypatch.setattr(global_settings, "log_retention_days", 14)

    try:
        setup_logging()
        logging.getLogger("tests.logging").info("file logging enabled")

        for handler in logging.getLogger().handlers:
            handler.flush()

        assert "file logging enabled" in (tmp_path / "app.log").read_text(encoding="utf-8")
    finally:
        for handler in logging.getLogger().handlers[:]:
            logging.getLogger().removeHandler(handler)
            handler.close()
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)
