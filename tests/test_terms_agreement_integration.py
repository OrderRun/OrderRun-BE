from __future__ import annotations

from app.core.security import create_access_token
from app.models.terms import TermsAgreement, TermsType
from app.models.user import User


def _payload(**overrides):
    data = {
        "termsOfService": True,
        "privacyPolicy": True,
        "paymentRefundPolicy": True,
    }
    data.update(overrides)
    return data


def test_terms_agreement_create_and_update(client, db, sample_user):
    token = create_access_token({"sub": str(sample_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post("/v1/terms", headers=headers, json=_payload())
    assert created.status_code == 201
    body = created.json()
    assert body["success"] is True
    assert body["message"] == "약관 동의가 완료되었습니다."
    assert body["data"]["userId"] == sample_user.id
    assert body["data"]["termsOfService"] is True
    assert body["data"]["privacyPolicy"] is True
    assert body["data"]["paymentRefundPolicy"] is True
    assert body["data"]["agreedAt"] is not None

    agreement = db.query(TermsAgreement).filter(TermsAgreement.user_id == sample_user.id).first()
    assert agreement is not None
    first_agreed_at = agreement.agreed_at

    updated = client.post("/v1/terms", headers=headers, json=_payload())
    assert updated.status_code == 201
    assert db.query(TermsAgreement).filter(TermsAgreement.user_id == sample_user.id).count() == 1
    db.refresh(agreement)
    assert agreement.agreed_at >= first_agreed_at


def test_terms_agreement_validation_errors(client, sample_user):
    token = create_access_token({"sub": str(sample_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    missing = client.post(
        "/v1/terms",
        headers=headers,
        json={"termsOfService": True, "privacyPolicy": True},
    )
    assert missing.status_code == 400
    assert missing.json()["error"]["code"] == "VALIDATION_ERROR"

    null_value = client.post(
        "/v1/terms",
        headers=headers,
        json=_payload(paymentRefundPolicy=None),
    )
    assert null_value.status_code == 400
    assert null_value.json()["error"]["code"] == "VALIDATION_ERROR"

    false_value = client.post(
        "/v1/terms",
        headers=headers,
        json=_payload(privacyPolicy=False),
    )
    assert false_value.status_code == 400
    assert false_value.json()["error"]["code"] == "VALIDATION_ERROR"


def test_terms_agreement_auth_errors(client, db):
    no_token = client.post("/v1/terms", json=_payload())
    assert no_token.status_code == 401
    assert no_token.json()["error"]["code"] == "INVALID_TOKEN"

    missing_user_token = create_access_token({"sub": "missing-user-id"})
    missing_user = client.post(
        "/v1/terms",
        headers={"Authorization": f"Bearer {missing_user_token}"},
        json=_payload(),
    )
    assert missing_user.status_code == 404
    assert missing_user.json()["error"]["code"] == "USER_NOT_FOUND"


def test_terms_agreement_model_spec_matches_docs():
    assert str(TermsAgreement.__table__.c.id.type).upper() == "BIGINT"
    assert str(TermsAgreement.__table__.c.user_id.type).upper() == "VARCHAR(36)"
    assert TermsAgreement.__table__.c.user_id.unique is True
    assert TermsAgreement.__table__.foreign_keys == set()

    required_terms = {terms_type.name for terms_type in TermsType if terms_type.required}
    assert required_terms == {
        "TERMS_OF_SERVICE",
        "PRIVACY_POLICY",
        "PAYMENT_REFUND_POLICY",
    }
