"""Add user soft delete and withdrawn user snapshots.

Revision ID: 0012_add_user_soft_delete_and_withdrawn_snapshots
Revises: 0011_add_proof_survey_question_id, 0007_remove_settlement_bank_code_and_holder
Create Date: 2026-06-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql


revision = "0012_add_user_soft_delete_and_withdrawn_snapshots"
down_revision = ("0011_add_proof_survey_question_id", "0007_remove_settlement_bank_code_and_holder")
branch_labels = None
depends_on = None

mysql_datetime = sa.DateTime(timezone=True).with_variant(mysql.DATETIME(fsp=6), "mysql")


def upgrade() -> None:
    bind = op.get_bind()
    existing_user_columns = _column_names(bind, "users")
    with op.batch_alter_table("users") as batch_op:
        if "deleted" not in existing_user_columns:
            batch_op.add_column(sa.Column("deleted", sa.Boolean(), nullable=False, server_default="0"))
        if "deleted_at" not in existing_user_columns:
            batch_op.add_column(sa.Column("deleted_at", mysql_datetime, nullable=True))

    if not _index_exists(bind, "users", "idx_users_deleted"):
        op.create_index("idx_users_deleted", "users", ["deleted"])

    if not sa.inspect(bind).has_table("withdrawn_user_snapshots"):
        op.create_table(
            "withdrawn_user_snapshots",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=True),
            sa.Column("phone", sa.String(length=20), nullable=True),
            sa.Column("phone_verified_at", mysql_datetime, nullable=True),
            sa.Column("last_login_at", mysql_datetime, nullable=True),
            sa.Column("user_created_at", mysql_datetime, nullable=True),
            sa.Column("withdrawn_at", mysql_datetime, nullable=False),
            sa.Column("anonymize_after", mysql_datetime, nullable=False),
            sa.Column("anonymized_at", mysql_datetime, nullable=True),
            sa.Column("created_at", mysql_datetime, nullable=False),
            sa.Column("updated_at", mysql_datetime, nullable=False),
        )

    for index_name, columns in (
        ("idx_withdrawn_user_snapshots_user_id", ["user_id"]),
        ("idx_withdrawn_user_snapshots_phone", ["phone"]),
        ("idx_withdrawn_user_snapshots_withdrawn_at", ["withdrawn_at"]),
        ("idx_withdrawn_user_snapshots_anonymize_after", ["anonymize_after"]),
    ):
        if not _index_exists(bind, "withdrawn_user_snapshots", index_name):
            op.create_index(index_name, "withdrawn_user_snapshots", columns)


def downgrade() -> None:
    bind = op.get_bind()
    for index_name in (
        "idx_withdrawn_user_snapshots_anonymize_after",
        "idx_withdrawn_user_snapshots_withdrawn_at",
        "idx_withdrawn_user_snapshots_phone",
        "idx_withdrawn_user_snapshots_user_id",
    ):
        if _index_exists(bind, "withdrawn_user_snapshots", index_name):
            op.drop_index(index_name, table_name="withdrawn_user_snapshots")

    if sa.inspect(bind).has_table("withdrawn_user_snapshots"):
        op.drop_table("withdrawn_user_snapshots")

    if _index_exists(bind, "users", "idx_users_deleted"):
        op.drop_index("idx_users_deleted", table_name="users")

    existing_user_columns = _column_names(bind, "users")
    with op.batch_alter_table("users") as batch_op:
        if "deleted_at" in existing_user_columns:
            batch_op.drop_column("deleted_at")
        if "deleted" in existing_user_columns:
            batch_op.drop_column("deleted")


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
