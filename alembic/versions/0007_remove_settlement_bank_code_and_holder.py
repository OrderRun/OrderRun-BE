"""Remove settlement bank code and account holder.

Revision ID: 0007_remove_settlement_bank_code_and_holder
Revises: 0006_remove_mission_status
Create Date: 2026-06-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0007_remove_settlement_bank_code_and_holder"
down_revision = "0006_remove_mission_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = _column_names(bind, "settlement_accounts")
    with op.batch_alter_table("settlement_accounts") as batch_op:
        if "bank_code" in existing:
            batch_op.drop_column("bank_code")
        if "account_holder" in existing:
            batch_op.drop_column("account_holder")


def downgrade() -> None:
    bind = op.get_bind()
    existing = _column_names(bind, "settlement_accounts")
    with op.batch_alter_table("settlement_accounts") as batch_op:
        if "bank_code" not in existing:
            batch_op.add_column(sa.Column("bank_code", sa.String(length=10), nullable=False, server_default="000"))
        if "account_holder" not in existing:
            batch_op.add_column(
                sa.Column("account_holder", sa.String(length=100), nullable=False, server_default="Unknown")
            )


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}
