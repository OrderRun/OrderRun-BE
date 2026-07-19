"""Create user withdrawal reason tables.

Revision ID: 0018_create_user_withdrawal_reasons
Revises: 0017_rename_offer_confirmation_timestamps
Create Date: 2026-07-19
"""

from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op


revision = "0018_create_user_withdrawal_reasons"
down_revision = "0017_rename_offer_confirmation_timestamps"
branch_labels = None
depends_on = None


REASONS = (
    ("원하는 임무가 많지 않았어요.", False),
    ("원하는 꼬봉(또는 행님)을 만나기 어려웠어요.", False),
    ("이용 방법이 어려웠어요.", False),
    ("앱이 자주 오류가 났어요.", False),
    ("다른 회원과 문제가 있었어요.", False),
    ("다른 서비스를 이용하려고 해요.", False),
    ("기타", True),
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("user_withdrawal_reason_questions"):
        op.create_table(
            "user_withdrawal_reason_questions",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("question_text", sa.String(length=500), nullable=False),
            sa.Column("display_order", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
            sa.Column("requires_detail", sa.Boolean(), server_default="0", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("display_order", name="uk_user_withdrawal_reason_questions_display_order"),
        )
        op.create_index(
            "idx_user_withdrawal_reason_questions_lookup",
            "user_withdrawal_reason_questions",
            ["is_active", "display_order", "id"],
        )
        now = datetime.now(timezone.utc)
        op.bulk_insert(
            sa.table(
                "user_withdrawal_reason_questions",
                sa.column("question_text", sa.String()),
                sa.column("display_order", sa.Integer()),
                sa.column("is_active", sa.Boolean()),
                sa.column("requires_detail", sa.Boolean()),
                sa.column("created_at", sa.DateTime()),
                sa.column("updated_at", sa.DateTime()),
            ),
            [
                {
                    "question_text": reason,
                    "display_order": index,
                    "is_active": True,
                    "requires_detail": requires_detail,
                    "created_at": now,
                    "updated_at": now,
                }
                for index, (reason, requires_detail) in enumerate(REASONS, start=1)
            ],
        )

    inspector = sa.inspect(bind)
    if not inspector.has_table("user_withdrawals"):
        op.create_table(
            "user_withdrawals",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("reason_question_id", sa.BigInteger(), nullable=True),
            sa.Column("detail_reason", sa.String(length=500), nullable=True),
            sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_user_withdrawals_user_id", "user_withdrawals", ["user_id"])
        op.create_index("ix_user_withdrawals_withdrawn_at", "user_withdrawals", ["withdrawn_at"])
        op.create_index("idx_user_withdrawals_reason_question_id", "user_withdrawals", ["reason_question_id"])
        op.create_index("idx_user_withdrawals_user_withdrawn_at", "user_withdrawals", ["user_id", "withdrawn_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("user_withdrawals"):
        op.drop_index("idx_user_withdrawals_user_withdrawn_at", table_name="user_withdrawals")
        op.drop_index("idx_user_withdrawals_reason_question_id", table_name="user_withdrawals")
        op.drop_index("ix_user_withdrawals_withdrawn_at", table_name="user_withdrawals")
        op.drop_index("ix_user_withdrawals_user_id", table_name="user_withdrawals")
        op.drop_table("user_withdrawals")

    inspector = sa.inspect(bind)
    if inspector.has_table("user_withdrawal_reason_questions"):
        op.drop_index(
            "idx_user_withdrawal_reason_questions_lookup",
            table_name="user_withdrawal_reason_questions",
        )
        op.drop_table("user_withdrawal_reason_questions")
