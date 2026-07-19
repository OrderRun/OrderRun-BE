from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.main import app
from app.models.dispute_evidence import DisputeEvidence
from app.models.notification import Notification
from app.models.offer import Offer, OfferStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.settlement import SettlementAccount
from app.models.terms import TermsAgreement
from app.models.user import (
    AuthPhoneVerification,
    PhoneVerificationPurpose,
    PhoneVerificationStatus,
    User,
    UserFCMToken,
    UserWithdrawal,
    UserWithdrawalReasonQuestion,
)
from app.services.sms_service import get_sms_sender
from app.services.proposal.proposal_service import ProposalService
from app.services.user_auth.phone_verification import VERIFICATION_CODE_MAX_ATTEMPTS
from app.services.user_auth.user_withdrawal_service import UserWithdrawalService


WITHDRAWAL_REASONS = (
    ("원하는 임무가 많지 않았어요.", False),
    ("원하는 꼬봉(또는 행님)을 만나기 어려웠어요.", False),
    ("이용 방법이 어려웠어요.", False),
    ("앱이 자주 오류가 났어요.", False),
    ("다른 회원과 문제가 있었어요.", False),
    ("다른 서비스를 이용하려고 해요.", False),
    ("기타", True),
)


def seed_withdrawal_reasons(db) -> list[UserWithdrawalReasonQuestion]:
    reasons = [
        UserWithdrawalReasonQuestion(
            question_text=text,
            display_order=index,
            requires_detail=requires_detail,
            is_active=True,
        )
        for index, (text, requires_detail) in enumerate(WITHDRAWAL_REASONS, start=1)
    ]
    db.add_all(reasons)
    db.commit()
    return reasons


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
    assert set(payload) == {"success", "data", "message"}
    assert payload["success"] is True
    assert payload["message"] is None
    assert payload["data"]["phone"] == "01012345678"
    assert payload["data"]["expiresAt"] is not None
    code = _extract_code(sms_sender.sent_messages[-1]["message"])
    confirm = client.post(
        "/v1/auth/signup/confirm",
        json={"phone": phone, "code": code},
    )
    assert confirm.status_code == 200
    confirm_payload = confirm.json()
    assert set(confirm_payload) == {"success", "data", "message"}
    assert confirm_payload["message"] is None
    return confirm_payload["data"]


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
    assert login_send.json()["message"] is None
    login_code = _extract_code(sms_sender.sent_messages[-1]["message"])

    login_confirm = client.post(
        "/v1/auth/login/confirm",
        json={"phone": "010-1234-5678", "code": login_code, "fcmToken": "  token-1  "},
    )
    assert login_confirm.status_code == 200
    login_payload = login_confirm.json()
    assert login_payload["message"] is None
    login_data = login_payload["data"]
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
    refresh_payload = refresh.json()
    assert refresh_payload["message"] is None
    refresh_data = refresh_payload["data"]
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


def test_signup_confirm_accepts_and_stores_fcm_token(client, db, sms_sender):
    signup_send = client.post(
        "/v1/auth/signup/send",
        json={"name": "홍길동", "phone": "010-1234-5678", "carrier": "SKT"},
    )
    assert signup_send.status_code == 200
    code = _extract_code(sms_sender.sent_messages[-1]["message"])

    signup_confirm = client.post(
        "/v1/auth/signup/confirm",
        json={"phone": "010-1234-5678", "code": code, "fcmToken": "  signup-token  "},
    )

    assert signup_confirm.status_code == 200
    signup_data = signup_confirm.json()["data"]
    assert signup_data["tokenType"] == "Bearer"
    assert signup_data["accessToken"]
    assert signup_data["refreshToken"]
    user = db.query(User).filter(User.phone == "01012345678").first()
    assert user is not None
    fcm = db.query(UserFCMToken).filter(UserFCMToken.user_id == user.id).first()
    assert fcm is not None
    assert fcm.fcm_token == "signup-token"


def test_signup_confirm_rejects_blank_fcm_token(client, sms_sender):
    signup_send = client.post(
        "/v1/auth/signup/send",
        json={"name": "홍길동", "phone": "010-1234-5678", "carrier": "SKT"},
    )
    assert signup_send.status_code == 200
    code = _extract_code(sms_sender.sent_messages[-1]["message"])

    signup_confirm = client.post(
        "/v1/auth/signup/confirm",
        json={"phone": "010-1234-5678", "code": code, "fcmToken": "   "},
    )

    assert signup_confirm.status_code == 400
    assert signup_confirm.json()["error"]["code"] == "VALIDATION_ERROR"


def test_login_confirm_succeeds_with_verification_bypass_code(client, sms_sender, monkeypatch):
    # given: 가입된 유저, 비프로덕션 환경
    _signup(client, sms_sender)
    monkeypatch.setattr("app.services.user_auth.phone_verification.settings.app_env", "development")
    sent_count = len(sms_sender.sent_messages)

    # when: 우회 인증 코드로 로그인 확인 요청
    response = client.post(
        "/v1/auth/login/confirm",
        json={"phone": "010-1234-5678", "code": "123456"},
    )

    # then: 로그인 성공, SMS 미전송
    assert response.status_code == 200
    assert response.json()["data"]["accessToken"]
    assert len(sms_sender.sent_messages) == sent_count


def test_login_confirm_returns_user_not_found_when_user_does_not_exist(client, monkeypatch):
    # given: 존재하지 않는 유저, 비프로덕션 환경
    monkeypatch.setattr("app.services.user_auth.phone_verification.settings.app_env", "development")

    # when: 우회 인증 코드로 로그인 확인 요청
    response = client.post(
        "/v1/auth/login/confirm",
        json={"phone": "010-9999-8888", "code": "123456"},
    )

    # then: 404 USER_NOT_FOUND
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "USER_NOT_FOUND"


def test_login_confirm_returns_not_found_when_no_pending_verification(client, sms_sender, monkeypatch):
    # given: 가입된 유저, 인증 요청 없음, 프로덕션 환경
    _signup(client, sms_sender)
    monkeypatch.setattr("app.services.user_auth.phone_verification.settings.app_env", "production")

    # when: 코드 확인 요청
    response = client.post(
        "/v1/auth/login/confirm",
        json={"phone": "010-1234-5678", "code": "123456"},
    )

    # then: 404 PHONE_VERIFICATION_NOT_FOUND
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PHONE_VERIFICATION_NOT_FOUND"


def test_login_confirm_returns_code_mismatch_when_wrong_code_submitted(client, db, sms_sender, monkeypatch):
    # given: 가입된 유저, 인증 요청 완료, 프로덕션 환경
    _signup(client, sms_sender)
    monkeypatch.setattr("app.services.user_auth.phone_verification.settings.app_env", "production")

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

    # when: 틀린 코드로 로그인 확인 요청
    response = client.post(
        "/v1/auth/login/confirm",
        json={"phone": "010-1234-5678", "code": "123456"},
    )

    # then: 400 PHONE_VERIFICATION_CODE_MISMATCH
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "PHONE_VERIFICATION_CODE_MISMATCH"


def test_signup_confirm_rejects_verification_bypass_code(client, db, sms_sender, monkeypatch):
    # given: 회원가입 인증 요청, 비프로덕션 환경
    monkeypatch.setattr("app.services.user_auth.phone_verification.settings.app_env", "development")

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

    # when: 우회 인증 코드로 회원가입 확인 요청
    response = client.post(
        "/v1/auth/signup/confirm",
        json={"phone": "010-5555-6666", "code": "123456"},
    )

    # then: 회원가입은 우회 코드를 허용하지 않으므로 400
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "PHONE_VERIFICATION_CODE_MISMATCH"


def test_user_detail_alarm_and_fcm_token_flow(client, db, sms_sender):
    _signup(client, sms_sender)
    user = db.query(User).filter(User.phone == "01012345678").first()
    assert user is not None

    from app.core.security import create_access_token

    token = create_access_token({"sub": str(user.id)})

    detail = client.get("/v1/user/detail", headers={"Authorization": f"Bearer {token}"})
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert set(detail_payload) == {"success", "data", "message"}
    assert detail_payload["message"] is None
    data = detail_payload["data"]
    assert data["id"] == user.id
    assert data["name"] == "홍길동"
    assert data["phone"] == "01012345678"
    assert data["alarmEnabled"] is False
    assert data["level"] == 0
    assert data["phoneVerifiedAt"] is not None

    alarm = client.patch(
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

    extra_alarm_field = client.patch(
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


def test_update_user_name_requires_auth_and_updates_only_current_user(client, db, factory):
    user = factory.user(phone="01012340001", name="기존닉네임")
    other_user = factory.user(phone="01012340002", name="다른사용자")

    unauthenticated = client.patch("/v1/user/name", json={"name": "인증없음"})
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["error"]["code"] == "INVALID_TOKEN"

    response = client.patch(
        "/v1/user/name",
        headers=factory.headers_for(user),
        json={"name": "  새닉네임  "},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "닉네임이 업데이트되었습니다."

    db.refresh(user)
    db.refresh(other_user)
    assert user.name == "새닉네임"
    assert other_user.name == "다른사용자"

    detail = client.get("/v1/user/detail", headers=factory.headers_for(user))
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload["message"] is None
    assert detail_payload["data"]["name"] == "새닉네임"
    assert detail_payload["data"]["phoneVerifiedAt"] is None
    assert detail_payload["data"]["lastLoginAt"] is None


def test_update_user_name_validation_errors(client, factory):
    user = factory.user(phone="01012340003", name="기존닉네임")
    headers = factory.headers_for(user)

    blank = client.patch("/v1/user/name", headers=headers, json={"name": "   "})
    assert blank.status_code == 400
    assert blank.json()["error"]["code"] == "VALIDATION_ERROR"

    too_long = client.patch("/v1/user/name", headers=headers, json={"name": "가" * 101})
    assert too_long.status_code == 400
    assert too_long.json()["error"]["code"] == "VALIDATION_ERROR"

    extra_field = client.patch(
        "/v1/user/name",
        headers=headers,
        json={"name": "새닉네임", "unexpected": True},
    )
    assert extra_field.status_code == 400
    assert extra_field.json()["error"]["code"] == "VALIDATION_ERROR"


def test_withdraw_user_hard_deletes_pii_and_keeps_anonymized_activity_history(client, db, factory):
    user = factory.user(phone="01012340004", name="탈퇴사용자")
    headers = factory.headers_for(user)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    user_id = user.id
    user_phone = user.phone

    proposal = factory.proposal(orderer_id=user_id, status=ProposalStatus.ALL_COMPLETED)
    offer = factory.offer(proposal_id=proposal.id, runner_id=user_id, status=OfferStatus.ALL_COMPLETED)
    evidence = DisputeEvidence(
        proposal_id=proposal.id,
        offer_id=offer.id,
        actor_id=user_id,
        survey_question_id=1,
        reason="탈퇴 전 분쟁 사유",
    )
    fcm_token = UserFCMToken(user_id=user_id, fcm_token="withdraw-token")
    settlement = SettlementAccount(
        user_id=user_id,
        bank_name="신한은행",
        account_holder="탈퇴사용자",
        encrypted_account_number="encrypted",
        masked_account_number="********1234",
    )
    terms = TermsAgreement(
        user_id=user_id,
        terms_of_service=True,
        privacy_policy=True,
        payment_refund_policy=True,
        agreed_at=now,
    )
    verification = AuthPhoneVerification(
        purpose=PhoneVerificationPurpose.LOGIN,
        phone=user_phone,
        code_hash="hash",
        status=PhoneVerificationStatus.VERIFIED,
        expires_at=now + timedelta(minutes=5),
        sent_at=now,
        verified_at=now,
        attempt_count=0,
    )
    notification = Notification(
        user_id=user_id,
        notification_type="custom",
        title="탈퇴 전 알림",
        body="탈퇴 전 알림 본문",
        status="sent",
    )
    db.add_all([evidence, fcm_token, settlement, terms, verification, notification])
    db.commit()

    response = client.delete("/v1/user", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"success": True, "data": None, "message": "회원 탈퇴가 완료되었습니다."}

    withdrawn_user = db.query(User).filter(User.id == user_id).first()
    assert withdrawn_user is not None
    assert withdrawn_user.deleted is True
    assert withdrawn_user.deleted_at is not None
    assert withdrawn_user.name is None
    assert withdrawn_user.phone is None
    assert withdrawn_user.phone_verified_at is None
    assert withdrawn_user.password_hash is None
    assert withdrawn_user.last_login_at is None
    assert withdrawn_user.alarm_enabled is None

    assert db.query(UserFCMToken).filter(UserFCMToken.user_id == user_id).first() is None
    assert db.query(AuthPhoneVerification).filter(AuthPhoneVerification.phone == user_phone).first() is None
    assert db.query(SettlementAccount).filter(SettlementAccount.user_id == user_id).first() is None
    assert db.query(TermsAgreement).filter(TermsAgreement.user_id == user_id).first() is not None
    assert db.query(Notification).filter(Notification.user_id == user_id).first() is None
    assert db.query(Proposal).filter(Proposal.id == proposal.id, Proposal.orderer_id == user_id).first() is not None
    assert db.query(Offer).filter(Offer.id == offer.id, Offer.runner_id == user_id).first() is not None
    assert db.query(DisputeEvidence).filter(
        DisputeEvidence.id == evidence.id,
        DisputeEvidence.actor_id == user_id,
    ).first() is not None

    activity_viewer = factory.user(phone="01012340012", name="조회사용자")
    proposal_detail = ProposalService.get_proposal_detail(db, proposal.id, activity_viewer.id)
    assert proposal_detail.orderer_name == "탈퇴한 사용자"
    assert proposal_detail.offers[0].runner_name == "탈퇴한 사용자"

    detail = client.get("/v1/user/detail", headers=headers)
    assert detail.status_code == 404
    assert detail.json()["error"]["code"] == "USER_NOT_FOUND"

    signup_send = client.post(
        "/v1/auth/signup/send",
        json={"name": "재가입사용자", "phone": user_phone, "carrier": "SKT"},
    )
    assert signup_send.status_code == 200
    withdrawal = db.query(UserWithdrawal).filter(UserWithdrawal.user_id == user_id).one()
    assert withdrawal.reason_question_id is None
    assert withdrawal.detail_reason is None
    assert withdrawal.withdrawn_at == withdrawn_user.deleted_at


def test_list_user_withdrawal_reasons_returns_active_ordered_questions(client, db, auth_headers):
    reasons = seed_withdrawal_reasons(db)
    db.add(
        UserWithdrawalReasonQuestion(
            question_text="비활성",
            display_order=8,
            requires_detail=False,
            is_active=False,
        )
    )
    db.commit()

    response = client.get("/v1/user/withdrawal-reasons", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"] == [
        {
            "id": reason.id,
            "questionText": reason.question_text,
            "displayOrder": reason.display_order,
            "requiresDetail": reason.requires_detail,
        }
        for reason in reasons
    ]


def test_withdraw_user_stores_optional_reason_and_detail(client, db, factory):
    reasons = seed_withdrawal_reasons(db)
    reason = reasons[0]
    user = factory.user(phone="01012340104", name="탈퇴사유사용자")
    headers = factory.headers_for(user)

    response = client.delete(
        "/v1/user",
        headers=headers,
        json={"reasonQuestionId": reason.id, "detailReason": " 임무가 부족했습니다. "},
    )

    assert response.status_code == 200
    withdrawal = db.query(UserWithdrawal).filter(UserWithdrawal.user_id == user.id).one()
    assert withdrawal.reason_question_id == reason.id
    assert withdrawal.detail_reason == "임무가 부족했습니다."


def test_withdraw_user_requires_detail_for_other_reason(client, db, factory):
    reasons = seed_withdrawal_reasons(db)
    other_reason = next(reason for reason in reasons if reason.requires_detail)
    user = factory.user(phone="01012340105", name="기타사유사용자")
    headers = factory.headers_for(user)

    response = client.delete("/v1/user", headers=headers, json={"reasonQuestionId": other_reason.id})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"] == "detailReason"
    db.refresh(user)
    assert user.deleted is False
    assert db.query(UserWithdrawal).filter(UserWithdrawal.user_id == user.id).first() is None


def test_withdraw_user_rejects_inactive_or_unknown_reason(client, db, factory):
    inactive_reason = UserWithdrawalReasonQuestion(
        question_text="비활성",
        display_order=1,
        requires_detail=False,
        is_active=False,
    )
    db.add(inactive_reason)
    db.commit()
    user = factory.user(phone="01012340106", name="비활성사유사용자")
    headers = factory.headers_for(user)

    response = client.delete("/v1/user", headers=headers, json={"reasonQuestionId": inactive_reason.id})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"] == "reasonQuestionId"
    db.refresh(user)
    assert user.deleted is False
    assert db.query(UserWithdrawal).filter(UserWithdrawal.user_id == user.id).first() is None


@pytest.mark.parametrize(
    "proposal_status",
    [ProposalStatus.HOLDING, ProposalStatus.POSTED, ProposalStatus.OFFERED],
)
def test_withdraw_user_auto_cancels_pre_match_proposal_and_waiting_offers(db, factory, proposal_status):
    user = factory.user(phone="01012340005", name="요청사용자")
    db.add(UserFCMToken(user_id=user.id, fcm_token="kept-token"))
    proposal = factory.proposal(orderer_id=user.id, status=proposal_status)
    waiting_offer = factory.offer(proposal_id=proposal.id, runner_id=factory.user(phone="01012340008").id)
    own_waiting_offer = factory.offer(
        proposal_id=factory.proposal(orderer_id=factory.user(phone="01012340009").id).id,
        runner_id=user.id,
    )
    db.commit()

    UserWithdrawalService.withdraw_user(db, user)

    db.refresh(proposal)
    db.refresh(waiting_offer)
    db.refresh(own_waiting_offer)
    db.refresh(user)
    assert proposal.status == ProposalStatus.CANCELLED
    assert waiting_offer.status == OfferStatus.CANCELLED
    assert own_waiting_offer.status == OfferStatus.CANCELLED
    assert user.deleted is True


@pytest.mark.parametrize(
    "proposal_status",
    [ProposalStatus.MATCHED, ProposalStatus.ORDER_COMPLETED, ProposalStatus.DISPUTED],
)
def test_withdraw_user_blocks_when_user_has_active_proposal(db, factory, proposal_status):
    user = factory.user(phone="01012340006", name="오더사용자")
    proposal = factory.proposal(orderer_id=user.id, status=proposal_status)

    with pytest.raises(HTTPException) as exc_info:
        UserWithdrawalService.withdraw_user(db, user)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "USER_WITHDRAWAL_BLOCKED"
    db.refresh(user)
    db.refresh(proposal)
    assert user.deleted is False
    assert proposal.status == proposal_status
    assert db.query(UserWithdrawal).filter(UserWithdrawal.user_id == user.id).first() is None


@pytest.mark.parametrize(
    "offer_status",
    [OfferStatus.ACCEPTED, OfferStatus.RUNNER_COMPLETED, OfferStatus.DISPUTED],
)
def test_withdraw_user_blocks_when_user_has_active_offer(db, factory, offer_status):
    user = factory.user(phone="01012340006", name="러너사용자")
    orderer = factory.user(phone="01012340007", name="오더사용자")
    proposal = factory.proposal(orderer_id=orderer.id, status=ProposalStatus.CANCELLED)
    offer = factory.offer(proposal_id=proposal.id, runner_id=user.id, status=offer_status)

    with pytest.raises(HTTPException) as exc_info:
        UserWithdrawalService.withdraw_user(db, user)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "USER_WITHDRAWAL_BLOCKED"
    db.refresh(user)
    db.refresh(offer)
    assert user.deleted is False
    assert offer.status == offer_status
    assert db.query(UserWithdrawal).filter(UserWithdrawal.user_id == user.id).first() is None


def test_withdraw_user_rolls_back_all_changes_when_anonymization_fails(db, factory, monkeypatch):
    user = factory.user(phone="01012340015", name="요청사용자")
    db.add(UserFCMToken(user_id=user.id, fcm_token="rollback-token"))
    proposal = factory.proposal(orderer_id=user.id, status=ProposalStatus.OFFERED)
    waiting_offer = factory.offer(proposal_id=proposal.id, runner_id=factory.user(phone="01012340016").id)
    db.commit()

    def fail_withdraw(self, withdrawn_at):
        raise RuntimeError("anonymization failed")

    monkeypatch.setattr(User, "withdraw", fail_withdraw)

    with pytest.raises(RuntimeError, match="anonymization failed"):
        UserWithdrawalService.withdraw_user(db, user)

    db.expire_all()
    assert db.query(User).filter(User.id == user.id, User.deleted.is_(False)).one()
    assert db.query(UserFCMToken).filter(UserFCMToken.user_id == user.id).one()
    assert db.query(Proposal).filter(Proposal.id == proposal.id).one().status == ProposalStatus.OFFERED
    assert db.query(Offer).filter(Offer.id == waiting_offer.id).one().status == OfferStatus.WAITING
    assert db.query(UserWithdrawal).filter(UserWithdrawal.user_id == user.id).first() is None


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

    verification.attempt_count = VERIFICATION_CODE_MAX_ATTEMPTS - 1
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
    verification.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
    db.commit()

    expired_confirm = client.post(
        "/v1/auth/signup/confirm",
        json={"phone": "010-2222-3333", "code": code},
    )
    assert expired_confirm.status_code == 400
    assert expired_confirm.json()["error"]["code"] == "PHONE_VERIFICATION_EXPIRED"


def test_signup_confirm_rolls_back_verification_when_user_becomes_duplicate(client, db, sms_sender, factory):
    phone = "01044445555"
    response = client.post(
        "/v1/auth/signup/send",
        json={"name": "홍길동", "phone": phone, "carrier": "SKT"},
    )
    assert response.status_code == 200
    code = _extract_code(sms_sender.sent_messages[-1]["message"])
    verification = db.query(AuthPhoneVerification).filter(
        AuthPhoneVerification.phone == phone,
        AuthPhoneVerification.purpose == PhoneVerificationPurpose.SIGNUP,
    ).one()
    factory.user(phone=phone)

    confirm = client.post("/v1/auth/signup/confirm", json={"phone": phone, "code": code})

    assert confirm.status_code == 409
    assert confirm.json()["error"]["code"] == "PHONE_ALREADY_EXISTS"
    db.refresh(verification)
    assert verification.status == PhoneVerificationStatus.PENDING
    assert verification.verified_at is None


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


def test_login_send_persists_verification_even_if_background_sms_fails(client, db, factory):
    class FailingSmsSender:
        def send(self, phone: str, message: str) -> None:
            raise RuntimeError("sms failed")

    user = factory.user(phone="01033334445")
    app.dependency_overrides[get_sms_sender] = lambda: FailingSmsSender()

    response = client.post("/v1/auth/login/send", json={"phone": user.phone})

    assert response.status_code == 200
    assert response.json()["data"]["phone"] == user.phone

    verification = db.query(AuthPhoneVerification).filter(
        AuthPhoneVerification.phone == user.phone,
        AuthPhoneVerification.purpose == PhoneVerificationPurpose.LOGIN,
    ).first()
    assert verification is not None
    assert verification.status == PhoneVerificationStatus.PENDING


def test_verification_send_does_not_persist_when_sms_sender_is_missing(client, db, factory):
    login_user = factory.user(phone="01033334446")
    app.dependency_overrides[get_sms_sender] = lambda: None

    signup_response = client.post(
        "/v1/auth/signup/send",
        json={"name": "홍길동", "phone": "010-3333-4447", "carrier": "SKT"},
    )
    login_response = client.post("/v1/auth/login/send", json={"phone": login_user.phone})

    assert signup_response.status_code == 500
    assert signup_response.json()["error"]["code"] == "SMS_SENDER_NOT_CONFIGURED"
    assert login_response.status_code == 500
    assert login_response.json()["error"]["code"] == "SMS_SENDER_NOT_CONFIGURED"
    assert db.query(AuthPhoneVerification).filter(
        AuthPhoneVerification.phone.in_(["01033334447", login_user.phone])
    ).count() == 0


def test_model_spec_matches_user_auth_docs():
    assert str(User.__table__.c.id.type).upper() == "VARCHAR(36)"
    assert str(User.__table__.c.phone.type).upper() == "VARCHAR(20)"
    assert User.__table__.c.phone.unique is True
    assert User.__table__.c.deleted.nullable is False
    assert User.__table__.c.deleted_at.nullable is True
    assert User.__table__.c.name.nullable is True
    assert User.__table__.c.alarm_enabled.nullable is True

    assert str(AuthPhoneVerification.__table__.c.id.type).upper() == "BIGINT"
    assert str(AuthPhoneVerification.__table__.c.code_hash.type).upper() == "VARCHAR(100)"
    assert AuthPhoneVerification.__table__.c.attempt_count.nullable is False
    assert AuthPhoneVerification.__table__.foreign_keys == set()

    assert str(UserFCMToken.__table__.c.id.type).upper() == "BIGINT"
    assert str(UserFCMToken.__table__.c.user_id.type).upper() == "VARCHAR(36)"
    assert UserFCMToken.__table__.c.user_id.unique is True
    assert UserFCMToken.__table__.foreign_keys == set()
