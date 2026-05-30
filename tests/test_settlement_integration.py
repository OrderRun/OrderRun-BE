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
            "bankCode": "004",
            "bankName": "국민은행",
            "accountNumber": "123456789012",
            "accountHolder": "홍길동",
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()["data"]
    assert created["bankCode"] == "004"
    assert created["bankName"] == "국민은행"
    assert created["maskedAccountNumber"] == "********9012"
    assert created["accountHolder"] == "홍길동"
    assert created["updatedAt"] is not None

    stored = db.query(SettlementAccount).filter(SettlementAccount.user_id == sample_user.id).one()
    assert stored.encrypted_account_number == "123456789012"

    update_response = client.put(
        "/v1/settlement/account",
        headers=auth_headers,
        json={
            "bankCode": "088",
            "bankName": "신한은행",
            "accountNumber": "987654321",
            "accountHolder": "김러너",
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()["data"]
    assert updated["bankCode"] == "088"
    assert updated["maskedAccountNumber"] == "*****4321"
    assert db.query(SettlementAccount).filter(SettlementAccount.user_id == sample_user.id).count() == 1


def test_settlement_account_validation_and_auth(client, auth_headers):
    unauthenticated = client.get("/v1/settlement/account")
    invalid = client.put(
        "/v1/settlement/account",
        headers=auth_headers,
        json={
            "bankCode": "A04",
            "bankName": " ",
            "accountNumber": "123",
            "accountHolder": " ",
        },
    )

    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["error"]["code"] == "INVALID_TOKEN"
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
