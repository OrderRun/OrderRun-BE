"""Restore settlement account holder.

Revision ID: 0013_restore_account_holder
Revises: 0012_add_user_soft_delete_and_withdrawn_snapshots
Create Date: 2026-06-19
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0013_restore_account_holder"
down_revision = "0012_add_user_soft_delete_and_withdrawn_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = _column_names(bind, "settlement_accounts")
    if "account_holder" in existing:
        return

    with op.batch_alter_table("settlement_accounts") as batch_op:
        batch_op.add_column(sa.Column("account_holder", sa.String(length=100), nullable=False, server_default="Unknown"))
        batch_op.alter_column("account_holder", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    existing = _column_names(bind, "settlement_accounts")
    if "account_holder" not in existing:
        return

    with op.batch_alter_table("settlement_accounts") as batch_op:
        batch_op.drop_column("account_holder")


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}
