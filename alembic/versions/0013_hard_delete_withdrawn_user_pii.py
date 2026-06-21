"""Hard delete withdrawn-user PII and remove snapshots.

Revision ID: 0013_hard_delete_withdrawn_user_pii
Revises: 0012_add_user_soft_delete_and_withdrawn_snapshots
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0013_hard_delete_withdrawn_user_pii"
down_revision = "0012_add_user_soft_delete_and_withdrawn_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("name", existing_type=sa.String(length=100), nullable=True)
        batch_op.alter_column("alarm_enabled", existing_type=sa.Boolean(), nullable=True)

    bind = op.get_bind()
    if sa.inspect(bind).has_table("withdrawn_user_snapshots"):
        op.drop_table("withdrawn_user_snapshots")


def downgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("withdrawn_user_snapshots"):
        op.create_table(
            "withdrawn_user_snapshots",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=True),
            sa.Column("phone", sa.String(length=20), nullable=True),
            sa.Column("phone_verified_at", sa.DateTime(), nullable=True),
            sa.Column("last_login_at", sa.DateTime(), nullable=True),
            sa.Column("user_created_at", sa.DateTime(), nullable=True),
            sa.Column("withdrawn_at", sa.DateTime(), nullable=False),
            sa.Column("anonymize_after", sa.DateTime(), nullable=False),
            sa.Column("anonymized_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("name", existing_type=sa.String(length=100), nullable=False)
        batch_op.alter_column("alarm_enabled", existing_type=sa.Boolean(), nullable=False)
