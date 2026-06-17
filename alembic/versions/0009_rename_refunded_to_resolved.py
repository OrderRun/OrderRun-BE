"""Rename refunded proposal and offer state to resolved.

Revision ID: 0009_rename_refunded_to_resolved
Revises: 0008_add_offer_open_chat_url
Create Date: 2026-06-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_rename_refunded_to_resolved"
down_revision = "0008_add_offer_open_chat_url"
branch_labels = None
depends_on = None


PROPOSAL_STATUSES = (
    "HOLDING",
    "POSTED",
    "OFFERED",
    "MATCHED",
    "ORDER_COMPLETED",
    "ALL_COMPLETED",
    "DISPUTED",
    "RESOLVED",
    "CANCELLED",
)
OFFER_STATUSES = (
    "WAITING",
    "ACCEPTED",
    "RUNNER_COMPLETED",
    "ALL_COMPLETED",
    "DISPUTED",
    "RESOLVED",
    "REJECTED",
    "CANCELLED",
)
PROPOSAL_STATUSES_WITH_REFUNDED = (*PROPOSAL_STATUSES[:-2], "REFUNDED", *PROPOSAL_STATUSES[-2:])
OFFER_STATUSES_WITH_REFUNDED = (*OFFER_STATUSES[:-2], "REFUNDED", *OFFER_STATUSES[-2:])


def upgrade() -> None:
    bind = op.get_bind()
    _rename_timestamp_column("proposals", "refunded_at", "resolved_at")
    _rename_timestamp_column("offers", "refunded_at", "resolved_at")

    if bind.dialect.name == "mysql":
        _alter_mysql_enum("proposals", "status", PROPOSAL_STATUSES_WITH_REFUNDED)
        _alter_mysql_enum("offers", "status", OFFER_STATUSES_WITH_REFUNDED)

    op.execute(sa.text("UPDATE proposals SET status = 'RESOLVED' WHERE status = 'REFUNDED'"))
    op.execute(sa.text("UPDATE offers SET status = 'RESOLVED' WHERE status = 'REFUNDED'"))

    if bind.dialect.name == "mysql":
        _alter_mysql_enum("proposals", "status", PROPOSAL_STATUSES)
        _alter_mysql_enum("offers", "status", OFFER_STATUSES)


def downgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name == "mysql":
        _alter_mysql_enum("proposals", "status", PROPOSAL_STATUSES_WITH_REFUNDED)
        _alter_mysql_enum("offers", "status", OFFER_STATUSES_WITH_REFUNDED)

    op.execute(sa.text("UPDATE proposals SET status = 'REFUNDED' WHERE status = 'RESOLVED'"))
    op.execute(sa.text("UPDATE offers SET status = 'REFUNDED' WHERE status = 'RESOLVED'"))

    if bind.dialect.name == "mysql":
        _alter_mysql_enum("proposals", "status", _replace_status(PROPOSAL_STATUSES, "RESOLVED", "REFUNDED"))
        _alter_mysql_enum("offers", "status", _replace_status(OFFER_STATUSES, "RESOLVED", "REFUNDED"))

    _rename_timestamp_column("proposals", "resolved_at", "refunded_at")
    _rename_timestamp_column("offers", "resolved_at", "refunded_at")


def _rename_timestamp_column(table_name: str, old_name: str, new_name: str) -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}
    if old_name not in columns:
        return
    if new_name in columns:
        op.execute(sa.text(f"UPDATE {table_name} SET {new_name} = {old_name} WHERE {new_name} IS NULL"))
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_column(old_name)
        return

    with op.batch_alter_table(table_name) as batch_op:
        batch_op.alter_column(
            old_name,
            new_column_name=new_name,
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=True,
        )


def _alter_mysql_enum(table_name: str, column_name: str, statuses: tuple[str, ...]) -> None:
    enum_values = ", ".join(f"'{status}'" for status in statuses)
    op.execute(sa.text(f"ALTER TABLE {table_name} MODIFY {column_name} ENUM({enum_values}) NOT NULL"))


def _replace_status(statuses: tuple[str, ...], old: str, new: str) -> tuple[str, ...]:
    return tuple(new if status == old else status for status in statuses)
