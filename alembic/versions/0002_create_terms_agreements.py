"""Create terms agreements table when missing.

Revision ID: 0002_create_terms_agreements
Revises: 0001_baseline
Create Date: 2026-06-01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql


revision = "0002_create_terms_agreements"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None

mysql_datetime = sa.DateTime(timezone=True).with_variant(mysql.DATETIME(fsp=6), "mysql")


def upgrade() -> None:
    bind = op.get_bind()

    op.create_table(
        "terms_agreements",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("terms_of_service", sa.Boolean(), nullable=False),
        sa.Column("privacy_policy", sa.Boolean(), nullable=False),
        sa.Column("payment_refund_policy", sa.Boolean(), nullable=False),
        sa.Column("agreed_at", mysql_datetime, nullable=False),
        sa.Column("created_at", mysql_datetime, nullable=False),
        sa.Column("updated_at", mysql_datetime, nullable=False),
        sa.UniqueConstraint("user_id", name="uq_terms_agreements_user_id"),
        if_not_exists=True,
    )
    if not _index_exists(bind, "terms_agreements", "idx_terms_agreements_user_id"):
        op.create_index(
            "idx_terms_agreements_user_id",
            "terms_agreements",
            ["user_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _index_exists(bind, "terms_agreements", "idx_terms_agreements_user_id"):
        op.drop_index("idx_terms_agreements_user_id", table_name="terms_agreements")
    if sa.inspect(bind).has_table("terms_agreements"):
        op.drop_table("terms_agreements")


def _index_exists(bind: sa.engine.Connection, table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return False
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))
