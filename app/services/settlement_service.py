"""Settlement account business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.settlement import SettlementAccount
from app.schemas.settlement import SettlementAccountRequest, SettlementAccountResponse


class SettlementService:
    """Service layer for settlement account storage."""

    @staticmethod
    def get_account(db: Session, user_id: str) -> SettlementAccountResponse | None:
        account = db.query(SettlementAccount).filter(SettlementAccount.user_id == user_id).first()
        if account is None:
            return None
        return SettlementService._to_response(account)

    @staticmethod
    def save_account(db: Session, user_id: str, request: SettlementAccountRequest) -> SettlementAccountResponse:
        account = db.query(SettlementAccount).filter(SettlementAccount.user_id == user_id).first()
        if account is None:
            account = SettlementAccount(user_id=user_id)
            db.add(account)

        account.bank_code = request.bank_code
        account.bank_name = request.bank_name
        account.account_holder = request.account_holder
        account.encrypted_account_number = request.account_number
        account.masked_account_number = SettlementService._mask_account_number(request.account_number)

        db.commit()
        db.refresh(account)
        return SettlementService._to_response(account)

    @staticmethod
    def _mask_account_number(account_number: str) -> str:
        if len(account_number) <= 4:
            return "*" * len(account_number)
        return f"{'*' * (len(account_number) - 4)}{account_number[-4:]}"

    @staticmethod
    def _to_response(account: SettlementAccount) -> SettlementAccountResponse:
        return SettlementAccountResponse(
            bank_code=account.bank_code,
            bank_name=account.bank_name,
            masked_account_number=account.masked_account_number,
            account_holder=account.account_holder,
            updated_at=account.updated_at,
        )
