"""Rename proofs to dispute evidences.

Revision ID: 0016_rename_proofs_to_dispute_evidences
Revises: 0015_create_proposal_reports
Create Date: 2026-06-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0016_rename_proofs_to_dispute_evidences"
down_revision = "0015_create_proposal_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "proofs"):
        if "proof_type" in _column_names(bind, "proofs"):
            bind.execute(sa.text("DELETE FROM proofs WHERE proof_type IS NULL OR proof_type != 'DISPUTE'"))
        if not _has_table(bind, "dispute_evidences"):
            op.rename_table("proofs", "dispute_evidences")

    if not _has_table(bind, "dispute_evidences"):
        return

    _drop_index_if_exists(bind, "dispute_evidences", "ix_proofs_proposal_id")
    _drop_index_if_exists(bind, "dispute_evidences", "ix_proofs_offer_id")
    _drop_index_if_exists(bind, "dispute_evidences", "ix_proofs_proof_type")
    _drop_index_if_exists(bind, "dispute_evidences", "idx_proofs_survey_question_id")
    _drop_column_if_exists(bind, "dispute_evidences", "proof_type")
    _drop_column_if_exists(bind, "dispute_evidences", "image_url")
    if "reason" in _column_names(bind, "dispute_evidences"):
        bind.execute(sa.text("UPDATE dispute_evidences SET reason = '' WHERE reason IS NULL"))
        op.alter_column("dispute_evidences", "reason", existing_type=sa.Text(), nullable=False)
    if "survey_question_id" in _column_names(bind, "dispute_evidences"):
        bind.execute(sa.text("UPDATE dispute_evidences SET survey_question_id = 0 WHERE survey_question_id IS NULL"))
        op.alter_column(
            "dispute_evidences",
            "survey_question_id",
            existing_type=sa.BigInteger(),
            nullable=False,
        )

    _create_index_if_missing(bind, "dispute_evidences", "ix_dispute_evidences_proposal_id", ["proposal_id"])
    _create_index_if_missing(bind, "dispute_evidences", "ix_dispute_evidences_offer_id", ["offer_id"])
    _create_index_if_missing(bind, "dispute_evidences", "ix_dispute_evidences_actor_id", ["actor_id"])
    _create_index_if_missing(
        bind,
        "dispute_evidences",
        "idx_dispute_evidences_survey_question_id",
        ["survey_question_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "dispute_evidences"):
        columns = _column_names(bind, "dispute_evidences")
        if "proof_type" not in columns:
            op.add_column(
                "dispute_evidences",
                sa.Column("proof_type", sa.String(length=30), nullable=False, server_default="DISPUTE"),
            )
        if "image_url" not in columns:
            op.add_column("dispute_evidences", sa.Column("image_url", sa.String(length=500), nullable=True))
        if "reason" in columns:
            op.alter_column("dispute_evidences", "reason", existing_type=sa.Text(), nullable=True)
        if "survey_question_id" in columns:
            op.alter_column(
                "dispute_evidences",
                "survey_question_id",
                existing_type=sa.BigInteger(),
                nullable=True,
            )
        if not _has_table(bind, "proofs"):
            op.rename_table("dispute_evidences", "proofs")

    if not _has_table(bind, "proofs"):
        return

    _drop_index_if_exists(bind, "proofs", "ix_dispute_evidences_proposal_id")
    _drop_index_if_exists(bind, "proofs", "ix_dispute_evidences_offer_id")
    _drop_index_if_exists(bind, "proofs", "ix_dispute_evidences_actor_id")
    _drop_index_if_exists(bind, "proofs", "idx_dispute_evidences_survey_question_id")
    _create_index_if_missing(bind, "proofs", "ix_proofs_proposal_id", ["proposal_id"])
    _create_index_if_missing(bind, "proofs", "ix_proofs_offer_id", ["offer_id"])
    _create_index_if_missing(bind, "proofs", "ix_proofs_proof_type", ["proof_type"])
    _create_index_if_missing(bind, "proofs", "idx_proofs_survey_question_id", ["survey_question_id"])


def _has_table(bind: sa.engine.Connection, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name)


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    if not _has_table(bind, table_name):
        return set()
    return {column["name"] for column in sa.inspect(bind).get_columns(table_name)}


def _index_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    if not _has_table(bind, table_name):
        return set()
    return {index["name"] for index in sa.inspect(bind).get_indexes(table_name)}


def _drop_column_if_exists(bind: sa.engine.Connection, table_name: str, column_name: str) -> None:
    if column_name in _column_names(bind, table_name):
        op.drop_column(table_name, column_name)


def _drop_index_if_exists(bind: sa.engine.Connection, table_name: str, index_name: str) -> None:
    if index_name in _index_names(bind, table_name):
        op.drop_index(index_name, table_name=table_name)


def _create_index_if_missing(
    bind: sa.engine.Connection,
    table_name: str,
    index_name: str,
    columns: list[str],
) -> None:
    if index_name not in _index_names(bind, table_name):
        op.create_index(index_name, table_name, columns)
