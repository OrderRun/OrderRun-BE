"""Remove mission amount snapshot fields.

Revision ID: 0003_remove_mission_amounts
Revises: 0002_create_terms_agreements
Create Date: 2026-06-01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0003_remove_mission_amounts"
down_revision = "0002_create_terms_agreements"
branch_labels = None
depends_on = None


REMOVED_COLUMNS = ("contract_amount", "run_fee", "item_price", "total_amount")


def upgrade() -> None:
    bind = op.get_bind()
    existing_columns = _column_names(bind, "missions")
    if not existing_columns:
        return
    with op.batch_alter_table("missions") as batch_op:
        for column_name in REMOVED_COLUMNS:
            if column_name in existing_columns:
                batch_op.drop_column(column_name)


def downgrade() -> None:
    bind = op.get_bind()
    existing_columns = _column_names(bind, "missions")
    if not existing_columns:
        return
    with op.batch_alter_table("missions") as batch_op:
        for column_name in REMOVED_COLUMNS:
            if column_name not in existing_columns:
                batch_op.add_column(sa.Column(column_name, sa.Integer(), nullable=False, server_default="0"))


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}
