"""Add user level.

Revision ID: 0007_add_user_level
Revises: 0006_remove_mission_status
Create Date: 2026-06-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0007_add_user_level"
down_revision = "0006_remove_mission_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = _column_names(bind, "users")
    if "level" in existing:
        return

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("level", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    bind = op.get_bind()
    existing = _column_names(bind, "users")
    if "level" not in existing:
        return

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("level")


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}
