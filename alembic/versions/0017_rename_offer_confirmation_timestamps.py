"""Rename confirmation timestamps for offers and proposals.

Revision ID: 0017_rename_offer_confirmation_timestamps
Revises: 0016_rename_proofs_to_dispute_evidences
Create Date: 2026-06-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0017_rename_offer_confirmation_timestamps"
down_revision = "0016_rename_proofs_to_dispute_evidences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Rename offer confirmation timestamps
    if _has_table(bind, "offers"):
        offer_columns = _column_names(bind, "offers")
        if "delivery_completed_at" in offer_columns and "runner_confirmed_at" not in offer_columns:
            op.alter_column(
                "offers",
                "delivery_completed_at",
                new_column_name="runner_confirmed_at",
                existing_type=sa.DateTime(timezone=True),
                nullable=True,
            )
        if "receipt_confirmed_at" in offer_columns and "orderer_confirmed_at" not in offer_columns:
            op.alter_column(
                "offers",
                "receipt_confirmed_at",
                new_column_name="orderer_confirmed_at",
                existing_type=sa.DateTime(timezone=True),
                nullable=True,
            )
        if "settled_at" in _column_names(bind, "offers"):
            op.drop_column("offers", "settled_at")

    # Rename proposal confirmation timestamps
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
        if "settled_at" in _column_names(bind, "proposals"):
            op.drop_column("proposals", "settled_at")


def downgrade() -> None:
    bind = op.get_bind()

    # Restore proposal confirmation timestamps
    if _has_table(bind, "proposals"):
        proposal_columns = _column_names(bind, "proposals")
        if "settled_at" not in proposal_columns:
            op.add_column("proposals", sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True))
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

    # Restore offer confirmation timestamps
    if _has_table(bind, "offers"):
        offer_columns = _column_names(bind, "offers")
        if "settled_at" not in offer_columns:
            op.add_column("offers", sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True))
        offer_columns = _column_names(bind, "offers")
        if "runner_confirmed_at" in offer_columns and "delivery_completed_at" not in offer_columns:
            op.alter_column(
                "offers",
                "runner_confirmed_at",
                new_column_name="delivery_completed_at",
                existing_type=sa.DateTime(timezone=True),
                nullable=True,
            )
        if "orderer_confirmed_at" in offer_columns and "receipt_confirmed_at" not in offer_columns:
            op.alter_column(
                "offers",
                "orderer_confirmed_at",
                new_column_name="receipt_confirmed_at",
                existing_type=sa.DateTime(timezone=True),
                nullable=True,
            )


def _has_table(bind: sa.engine.Connection, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name)


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    if not _has_table(bind, table_name):
        return set()
    return {column["name"] for column in sa.inspect(bind).get_columns(table_name)}
