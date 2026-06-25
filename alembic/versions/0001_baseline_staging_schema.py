"""Baseline existing staging schema.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-01
"""

from __future__ import annotations

from alembic import op

from app.core.database import Base

# Import models so Base.metadata includes every baseline table.
from app.models import offer, proposal, settlement, user  # noqa: F401

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None

BASELINE_TABLES = (
    "users",
    "auth_phone_verifications",
    "user_fcm_tokens",
    "proposals",
    "offers",
    "settlement_accounts",
)


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind(), tables=_baseline_tables(), checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), tables=_baseline_tables(), checkfirst=True)


def _baseline_tables() -> list:
    return [Base.metadata.tables[table_name] for table_name in BASELINE_TABLES]
