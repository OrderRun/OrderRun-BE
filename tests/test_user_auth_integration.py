from __future__ import annotations

import re
from datetime import datetime, timezone

from app.main import app
from app.models.user import AuthPhoneVerification, PhoneVerificationPurpose, PhoneVerificationStatus, User, UserFCMToken
from app.services.sms_service import get_sms_sender


def _extract_code(message: str) -> str:
    match = re.search(r"(\d{6})", message)
    assert match is not None
    return match.group(1)


def _signup(client, sms_sender, name="홍길동", phone="010-1234-5678", carrier="SKT"):
    response = client.post(
        "/v1/auth/signup/send",
        json={"name": name, "phone": phone, "carrier": carrier},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["phone"] == "01012345678"
    assert payload["data"]["expiresAt"] is not None
    code = _extract_code(sms_sender.sent_messages[-1]["message"])
    confirm = client.post(
        "/v1/auth/signup/confirm",
        json={"phone": phone, "code": code},
    )
    assert confirm.status_code == 200
    return confirm.json()["data"]


def test_signup_login_refresh_and_logout_flow(client, db, sms_sender):
    signup_data = _signup(client, sms_sender)

    user = db.query(User).filter(User.phone == "01012345678").first()
    assert user is not None
    assert user.name == "홍길동"
    assert user.phone_verified_at is not None
    assert user.last_login_at is not None
    assert user.alarm_enabled is False

    login_send = client.post("/v1/auth/login/send", json={"phone": "010-1234-5678"})
    assert login_send.status_code == 200
    login_code = _extract_code(sms_sender.sent_messages[-1]["message"])

    login_confirm = client.post(
        "/v1/auth/login/confirm",
        json={"phone": "010-1234-5678", "code": login_code, "fcmToken": "  token-1  "},
    )
    assert login_confirm.status_code == 200
    login_data = login_confirm.json()["data"]
    assert login_data["userId"] == signup_data["userId"]
    assert login_data["tokenType"] == "Bearer"
    assert login_data["expiresIn"] > 0
    assert login_data["accessToken"]
    assert login_data["refreshToken"]

    fcm = db.query(UserFCMToken).filter(UserFCMToken.user_id == user.id).first()
    assert fcm is not None
    assert fcm.fcm_token == "token-1"

    refresh = client.post(
        "/v1/auth/refresh",
        json={"refreshToken": login_data["refreshToken"]},
    )
    assert refresh.status_code == 200
    refresh_data = refresh.json()["data"]
    assert refresh_data["accessToken"]
    assert refresh_data["expiresIn"] > 0

    logout = client.post(
        "/v1/auth/logout",
        headers={"Authorization": f"Bearer {login_data['accessToken']}"},
        json={"refreshToken": login_data["refreshToken"]},
    )
    assert logout.status_code == 200
    assert logout.json()["message"] == "로그아웃 되었습니다."
    assert logout.json()["data"] is None


def test_login_confirm_accepts_test_code_in_development(client, sms_sender, monkeypatch):
    _signup(client, sms_sender)
    monkeypatch.setattr("app.services.user_auth_service.settings.app_env", "development")
    sent_count = len(sms_sender.sent_messages)

    login_confirm = client.post(
        "/v1/auth/login/confirm",
        json={"phone": "010-1234-5678", "code": "123456"},
    )

    assert login_confirm.status_code == 200
    assert login_confirm.json()["data"]["accessToken"]
    assert len(sms_sender.sent_messages) == sent_count


def test_login_confirm_accepts_test_code_in_staging(client, sms_sender, monkeypatch):
    _signup(client, sms_sender)
    monkeypatch.setattr("app.services.user_auth_service.settings.app_env", "staging")

    login_confirm = client.post(
        "/v1/auth/login/confirm",
        json={"phone": "010-1234-5678", "code": "123456"},
    )

    assert login_confirm.status_code == 200
    assert login_confirm.json()["data"]["accessToken"]


def test_login_confirm_rejects_test_code_for_missing_user_in_development(client, monkeypatch):
    monkeypatch.setattr("app.services.user_auth_service.settings.app_env", "development")

    login_confirm = client.post(
        "/v1/auth/login/confirm",
        json={"phone": "010-9999-8888", "code": "123456"},
    )

    assert login_confirm.status_code == 404
    assert login_confirm.json()["error"]["code"] == "USER_NOT_FOUND"


def test_login_confirm_rejects_test_code_without_pending_verification_in_production(client, sms_sender, monkeypatch):
    _signup(client, sms_sender)
    monkeypatch.setattr("app.services.user_auth_service.settings.app_env", "production")

    login_confirm = client.post(
        "/v1/auth/login/confirm",
        json={"phone": "010-1234-5678", "code": "123456"},
    )

    assert login_confirm.status_code == 404
    assert login_confirm.json()["error"]["code"] == "PHONE_VERIFICATION_NOT_FOUND"


def test_login_confirm_rejects_test_code_in_production(client, db, sms_sender, monkeypatch):
    _signup(client, sms_sender)
    monkeypatch.setattr("app.services.user_auth_service.settings.app_env", "production")

    login_send = client.post("/v1/auth/login/send", json={"phone": "010-1234-5678"})
    assert login_send.status_code == 200
    actual_code = _extract_code(sms_sender.sent_messages[-1]["message"])
    if actual_code == "123456":
        verification = db.query(AuthPhoneVerification).filter(
            AuthPhoneVerification.phone == "01012345678",
            AuthPhoneVerification.purpose == PhoneVerificationPurpose.LOGIN,
            AuthPhoneVerification.status == PhoneVerificationStatus.PENDING,
        ).order_by(AuthPhoneVerification.id.desc()).first()
        assert verification is not None
        verification.code_hash = "not-the-test-code-hash"
        db.commit()

    login_confirm = client.post(
        "/v1/auth/login/confirm",
        json={"phone": "010-1234-5678", "code": "123456"},
    )

    assert login_confirm.status_code == 400
    assert login_confirm.json()["error"]["code"] == "PHONE_VERIFICATION_CODE_MISMATCH"


def test_signup_confirm_does_not_accept_login_test_code(client, db, sms_sender, monkeypatch):
    monkeypatch.setattr("app.services.user_auth_service.settings.app_env", "development")

    signup_send = client.post(
        "/v1/auth/signup/send",
        json={"name": "홍길동", "phone": "010-5555-6666", "carrier": "SKT"},
    )
    assert signup_send.status_code == 200
    actual_code = _extract_code(sms_sender.sent_messages[-1]["message"])
    if actual_code == "123456":
        verification = db.query(AuthPhoneVerification).filter(
            AuthPhoneVerification.phone == "01055556666",
            AuthPhoneVerification.purpose == PhoneVerificationPurpose.SIGNUP,
            AuthPhoneVerification.status == PhoneVerificationStatus.PENDING,
        ).first()
        assert verification is not None
        verification.code_hash = "not-the-test-code-hash"
        db.commit()

    signup_confirm = client.post(
        "/v1/auth/signup/confirm",
        json={"phone": "010-5555-6666", "code": "123456"},
    )

    assert signup_confirm.status_code == 400
    assert signup_confirm.json()["error"]["code"] == "PHONE_VERIFICATION_CODE_MISMATCH"


def test_user_detail_alarm_and_fcm_token_flow(client, db, sms_sender):
    _signup(client, sms_sender)
    user = db.query(User).filter(User.phone == "01012345678").first()
    assert user is not None

    from app.core.security import create_access_token

    token = create_access_token({"sub": str(user.id)})

    detail = client.get("/v1/user/detail", headers={"Authorization": f"Bearer {token}"})
    assert detail.status_code == 200
    data = detail.json()["data"]
    assert data["id"] == user.id
    assert data["name"] == "홍길동"
    assert data["phone"] == "01012345678"
    assert data["alarmEnabled"] is False
    assert data["phoneVerifiedAt"] is not None

    alarm = client.post(
        "/v1/user/alarm",
        headers={"Authorization": f"Bearer {token}"},
        json={"alarmEnabled": True},
    )
    assert alarm.status_code == 200
    assert alarm.json()["message"] == "알람 설정이 업데이트되었습니다."
    db.refresh(user)
    assert user.alarm_enabled is True

    fcm = client.patch(
        "/v1/user/fcm-token",
        headers={"Authorization": f"Bearer {token}"},
        json={"fcmToken": "   token-2   "},
    )
    assert fcm.status_code == 200
    assert fcm.json()["message"] == "FCM 토큰이 업데이트되었습니다."
    token_row = db.query(UserFCMToken).filter(UserFCMToken.user_id == user.id).first()
    assert token_row is not None
    assert token_row.fcm_token == "token-2"

    second_fcm = client.patch(
        "/v1/user/fcm-token",
        headers={"Authorization": f"Bearer {token}"},
        json={"fcmToken": "token-3"},
    )
    assert second_fcm.status_code == 200
    assert db.query(UserFCMToken).filter(UserFCMToken.user_id == user.id).count() == 1
    db.refresh(token_row)
    assert token_row.fcm_token == "token-3"

    extra_alarm_field = client.post(
        "/v1/user/alarm",
        headers={"Authorization": f"Bearer {token}"},
        json={"alarmEnabled": True, "unexpected": True},
    )
    assert extra_alarm_field.status_code == 400
    assert extra_alarm_field.json()["error"]["code"] == "VALIDATION_ERROR"

    blank_fcm = client.patch(
        "/v1/user/fcm-token",
        headers={"Authorization": f"Bearer {token}"},
        json={"fcmToken": "   "},
    )
    assert blank_fcm.status_code == 400
    assert blank_fcm.json()["error"]["code"] == "VALIDATION_ERROR"


def test_verification_state_rules(client, db, sms_sender):
    first = client.post(
        "/v1/auth/signup/send",
        json={"name": "홍길동", "phone": "010-2222-3333", "carrier": "KT"},
    )
    assert first.status_code == 200
    duplicate = client.post(
        "/v1/auth/signup/send",
        json={"name": "홍길동", "phone": "01022223333", "carrier": "KT"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "PHONE_VERIFICATION_ALREADY_SENT"

    verification = db.query(AuthPhoneVerification).filter(
        AuthPhoneVerification.phone == "01022223333",
        AuthPhoneVerification.purpose == PhoneVerificationPurpose.SIGNUP,
    ).first()
    assert verification is not None
    assert verification.status == PhoneVerificationStatus.PENDING
    assert verification.carrier == "KT"

    mismatch = client.post(
        "/v1/auth/signup/confirm",
        json={"phone": "010-2222-3333", "code": "000000"},
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["error"]["code"] == "PHONE_VERIFICATION_CODE_MISMATCH"

    db.refresh(verification)
    assert verification.attempt_count == 1

    verification.attempt_count = 4
    db.commit()

    mismatch_again = client.post(
        "/v1/auth/signup/confirm",
        json={"phone": "010-2222-3333", "code": "111111"},
    )
    assert mismatch_again.status_code == 400
    db.refresh(verification)
    assert verification.status == PhoneVerificationStatus.EXPIRED

    expired = client.post(
        "/v1/auth/signup/send",
        json={"name": "홍길동", "phone": "010-2222-3333", "carrier": "KT"},
    )
    assert expired.status_code == 200
    code = _extract_code(sms_sender.sent_messages[-1]["message"])
    verification = db.query(AuthPhoneVerification).filter(
        AuthPhoneVerification.phone == "01022223333",
        AuthPhoneVerification.purpose == PhoneVerificationPurpose.SIGNUP,
        AuthPhoneVerification.status == PhoneVerificationStatus.PENDING,
    ).order_by(AuthPhoneVerification.id.desc()).first()
    assert verification is not None
    verification.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - datetime.resolution
    db.commit()

    expired_confirm = client.post(
        "/v1/auth/signup/confirm",
        json={"phone": "010-2222-3333", "code": code},
    )
    assert expired_confirm.status_code == 400
    assert expired_confirm.json()["error"]["code"] == "PHONE_VERIFICATION_EXPIRED"


def test_signup_send_persists_verification_even_if_background_sms_fails(client, db):
    class FailingSmsSender:
        def send(self, phone: str, message: str) -> None:
            raise RuntimeError("sms failed")

    app.dependency_overrides[get_sms_sender] = lambda: FailingSmsSender()

    response = client.post(
        "/v1/auth/signup/send",
        json={"name": "홍길동", "phone": "010-3333-4444", "carrier": "SKT"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["phone"] == "01033334444"

    verification = db.query(AuthPhoneVerification).filter(
        AuthPhoneVerification.phone == "01033334444",
        AuthPhoneVerification.purpose == PhoneVerificationPurpose.SIGNUP,
    ).first()
    assert verification is not None
    assert verification.status == PhoneVerificationStatus.PENDING


def test_model_spec_matches_user_auth_docs():
    assert str(User.__table__.c.id.type).upper() == "VARCHAR(36)"
    assert str(User.__table__.c.phone.type).upper() == "VARCHAR(20)"
    assert User.__table__.c.phone.unique is True

    assert str(AuthPhoneVerification.__table__.c.id.type).upper() == "BIGINT"
    assert str(AuthPhoneVerification.__table__.c.code_hash.type).upper() == "VARCHAR(100)"
    assert AuthPhoneVerification.__table__.c.attempt_count.nullable is False
    assert AuthPhoneVerification.__table__.foreign_keys == set()

    assert str(UserFCMToken.__table__.c.id.type).upper() == "BIGINT"
    assert str(UserFCMToken.__table__.c.user_id.type).upper() == "VARCHAR(36)"
    assert UserFCMToken.__table__.c.user_id.unique is True
    assert UserFCMToken.__table__.foreign_keys == set()
