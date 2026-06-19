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
    bind = op.get_bind()
    existing = _column_names(bind, "proofs")
    if "survey_question_id" not in existing:
        op.add_column("proofs", sa.Column("survey_question_id", sa.BigInteger(), nullable=True))
    if not _index_exists(bind, "proofs", "idx_proofs_survey_question_id"):
        op.create_index("idx_proofs_survey_question_id", "proofs", ["survey_question_id"])


def downgrade() -> None:
    bind = op.get_bind()
    if _index_exists(bind, "proofs", "idx_proofs_survey_question_id"):
        op.drop_index("idx_proofs_survey_question_id", table_name="proofs")

    existing = _column_names(bind, "proofs")
    if "survey_question_id" in existing:
        op.drop_column("proofs", "survey_question_id")


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_exists(bind: sa.engine.Connection, table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return False
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))
