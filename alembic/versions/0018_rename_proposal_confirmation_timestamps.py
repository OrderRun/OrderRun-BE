"""Rename proposal confirmation timestamps.

Revision ID: 0018_rename_proposal_confirmation_timestamps
Revises: 0017_rename_offer_confirmation_timestamps
Create Date: 2026-06-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0018_rename_proposal_confirmation_timestamps"
down_revision = "0017_rename_offer_confirmation_timestamps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "proposals"):
        proposal_columns = _column_names(bind, "proposals")
        if "delivery_reported_at" in proposal_columns and "runner_confirmed_at" not in proposal_columns:
            op.alter_column(
                "proposals",
                "delivery_reported_at",
                new_column_name="runner_confirmed_at",
                existing_type=sa.DateTime(timezone=True),
                nullable=True,
            )
        if "received_confirmed_at" in proposal_columns and "orderer_confirmed_at" not in proposal_columns:
            op.alter_column(
                "proposals",
                "received_confirmed_at",
                new_column_name="orderer_confirmed_at",
                existing_type=sa.DateTime(timezone=True),
                nullable=True,
            )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "proposals"):
        proposal_columns = _column_names(bind, "proposals")
        if "runner_confirmed_at" in proposal_columns and "delivery_reported_at" not in proposal_columns:
            op.alter_column(
                "proposals",
                "runner_confirmed_at",
                new_column_name="delivery_reported_at",
                existing_type=sa.DateTime(timezone=True),
                nullable=True,
            )
        if "orderer_confirmed_at" in proposal_columns and "received_confirmed_at" not in proposal_columns:
            op.alter_column(
                "proposals",
                "orderer_confirmed_at",
                new_column_name="received_confirmed_at",
                existing_type=sa.DateTime(timezone=True),
                nullable=True,
            )


def _has_table(bind: sa.engine.Connection, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name)


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    if not _has_table(bind, table_name):
        return set()
    return {column["name"] for column in sa.inspect(bind).get_columns(table_name)}
