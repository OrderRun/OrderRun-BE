"""Baseline existing staging schema.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-01
"""

from __future__ import annotations

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing staging databases should be attached with:
    # alembic stamp 0001_baseline
    pass


def downgrade() -> None:
    pass
