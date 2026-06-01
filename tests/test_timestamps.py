from __future__ import annotations

from datetime import datetime

from app.models.user import AuthPhoneVerification, PhoneVerificationPurpose, PhoneVerificationStatus


def test_auth_phone_verification_timestamps_are_orm_managed(db):
    created_at_column = AuthPhoneVerification.__table__.c.created_at
    updated_at_column = AuthPhoneVerification.__table__.c.updated_at
    assert created_at_column.default is not None
    assert created_at_column.server_default is None
    assert updated_at_column.default is not None
    assert updated_at_column.onupdate is not None
    assert updated_at_column.server_default is None

    verification = AuthPhoneVerification(
        purpose=PhoneVerificationPurpose.SIGNUP,
        phone="01012345678",
        name="홍길동",
        carrier="SKT",
        code_hash="hash",
        status=PhoneVerificationStatus.PENDING,
        expires_at=datetime(2026, 1, 1),
        sent_at=datetime(2026, 1, 1),
        attempt_count=0,
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)

    assert verification.created_at is not None
    assert verification.updated_at is not None
