from __future__ import annotations

from app.models.settlement import SettlementAccount


def test_get_settlement_account_returns_null_when_missing(client, auth_headers):
    response = client.get("/v1/settlement/account", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": None,
        "message": "Success",
    }


def test_save_and_update_settlement_account(client, db, auth_headers, sample_user):
    create_response = client.put(
        "/v1/settlement/account",
        headers=auth_headers,
        json={
            "bankName": "국민은행",
            "accountNumber": "123456789012",
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()["data"]
    assert created["bankName"] == "국민은행"
    assert created["maskedAccountNumber"] == "********9012"
    assert "bankCode" not in created
    assert "accountHolder" not in created
    assert created["updatedAt"] is not None

    stored = db.query(SettlementAccount).filter(SettlementAccount.user_id == sample_user.id).one()
    assert stored.encrypted_account_number == "123456789012"

    update_response = client.put(
        "/v1/settlement/account",
        headers=auth_headers,
        json={
            "bankName": "신한은행",
            "accountNumber": "987654321",
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()["data"]
    assert updated["bankName"] == "신한은행"
    assert updated["maskedAccountNumber"] == "*****4321"
    assert db.query(SettlementAccount).filter(SettlementAccount.user_id == sample_user.id).count() == 1


def test_get_settlement_bank_names_requires_auth_and_returns_supported_names(client, auth_headers):
    unauthenticated = client.get("/v1/settlement/banks")
    response = client.get("/v1/settlement/banks", headers=auth_headers)

    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["error"]["code"] == "INVALID_TOKEN"
    assert response.status_code == 200
    bank_names = response.json()["data"]["bankNames"]
    assert "국민은행" in bank_names
    assert "신한은행" in bank_names


def test_settlement_account_validation_and_auth(client, auth_headers):
    unauthenticated = client.get("/v1/settlement/account")
    invalid = client.put(
        "/v1/settlement/account",
        headers=auth_headers,
        json={
            "bankName": " ",
            "accountNumber": "123",
        },
    )

    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["error"]["code"] == "INVALID_TOKEN"
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"


def test_settlement_account_rejects_removed_fields_and_unsupported_bank(client, auth_headers):
    removed_fields = client.put(
        "/v1/settlement/account",
        headers=auth_headers,
        json={
            "bankCode": "004",
            "bankName": "국민은행",
            "accountNumber": "123456789012",
            "accountHolder": "홍길동",
        },
    )
    unsupported_bank = client.put(
        "/v1/settlement/account",
        headers=auth_headers,
        json={
            "bankName": "없는은행",
            "accountNumber": "123456789012",
        },
    )

    assert removed_fields.status_code == 400
    assert removed_fields.json()["error"]["code"] == "VALIDATION_ERROR"
    assert unsupported_bank.status_code == 400
    assert unsupported_bank.json()["error"]["code"] == "VALIDATION_ERROR"
