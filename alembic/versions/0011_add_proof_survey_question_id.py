"""Add survey question reference to proofs.

Revision ID: 0011_add_proof_survey_question_id
Revises: 0010_create_dispute_survey_questions
Create Date: 2026-06-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0011_add_proof_survey_question_id"
down_revision = "0010_create_dispute_survey_questions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("proofs", sa.Column("survey_question_id", sa.BigInteger(), nullable=True))
    op.create_index("idx_proofs_survey_question_id", "proofs", ["survey_question_id"])


def downgrade() -> None:
    op.drop_index("idx_proofs_survey_question_id", table_name="proofs")
    op.drop_column("proofs", "survey_question_id")
