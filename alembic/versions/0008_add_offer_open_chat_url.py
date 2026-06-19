"""Add offer open chat URL.

Revision ID: 0008_add_offer_open_chat_url
Revises: 0007_add_user_level
Create Date: 2026-06-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0008_add_offer_open_chat_url"
down_revision = "0007_add_user_level"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = _column_names(bind, "offers")
    if "open_chat_url" in existing:
        return

    with op.batch_alter_table("offers") as batch_op:
        batch_op.add_column(sa.Column("open_chat_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    existing = _column_names(bind, "offers")
    if "open_chat_url" not in existing:
        return

    with op.batch_alter_table("offers") as batch_op:
        batch_op.drop_column("open_chat_url")


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}
