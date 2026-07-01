from datetime import timedelta

import pytest

from app.core import security
from app.services.user_auth import phone_verification


def test_generate_verification_code_returns_six_digits(monkeypatch):
    monkeypatch.setattr(phone_verification.secrets, "randbelow", lambda _: 42)

    assert phone_verification.generate_verification_code() == "000042"


def test_hash_verification_code_is_stable_and_code_specific():
    first_hash = phone_verification.hash_verification_code("123456")

    assert first_hash == phone_verification.hash_verification_code("123456")
    assert first_hash != phone_verification.hash_verification_code("654321")


def test_verification_code_ttl_and_message_share_policy():
    assert phone_verification.VERIFICATION_CODE_TTL == timedelta(
        minutes=phone_verification.VERIFICATION_CODE_TTL_MINUTES
    )
    assert (
        f"{phone_verification.VERIFICATION_CODE_TTL_MINUTES}분 내 입력해 주세요."
        in phone_verification.build_verification_message("123456")
    )


def test_verification_code_max_attempts_policy():
    assert phone_verification.VERIFICATION_CODE_MAX_ATTEMPTS == 5


@pytest.mark.parametrize("app_env", ["development", "local", "staging"])
def test_login_test_code_is_allowed_in_non_production_environments(monkeypatch, app_env):
    monkeypatch.setattr(phone_verification.settings, "app_env", app_env)

    assert phone_verification.is_login_test_code_allowed("123456") is True


def test_login_test_code_is_rejected_in_production(monkeypatch):
    monkeypatch.setattr(phone_verification.settings, "app_env", "production")

    assert phone_verification.is_login_test_code_allowed("123456") is False


def test_access_token_expiration_is_converted_to_milliseconds(monkeypatch):
    monkeypatch.setattr(security.settings, "jwt_access_token_expire_minutes", 30)

    assert security.access_token_expires_in_ms() == 30 * 60 * 1000
