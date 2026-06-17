"""Create dispute survey questions table.

Revision ID: 0010_create_dispute_survey_questions
Revises: 0009_rename_refunded_to_resolved
Create Date: 2026-06-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0010_create_dispute_survey_questions"
down_revision = "0009_rename_refunded_to_resolved"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dispute_survey_questions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("target_type", sa.Enum("ORDER", "RUNNER", name="disputesurveytargettype"), nullable=False),
        sa.Column("question_text", sa.String(length=500), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("target_type", "display_order", name="uk_dispute_survey_questions_target_order"),
    )
    op.create_index(
        "idx_dispute_survey_questions_lookup",
        "dispute_survey_questions",
        ["target_type", "is_active", "display_order", "id"],
    )


def downgrade() -> None:
    op.drop_index("idx_dispute_survey_questions_lookup", table_name="dispute_survey_questions")
    op.drop_table("dispute_survey_questions")
