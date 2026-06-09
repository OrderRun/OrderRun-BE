"""Add retry_count to notifications; convert notification_type/status ENUM to VARCHAR.

Revision ID: 0004_notification_retry_types
Revises: 0003_remove_mission_amounts
Create Date: 2026-06-02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0004_notification_retry_types"
down_revision = "0003_remove_mission_amounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("notifications"):
        return

    existing = {col["name"] for col in inspector.get_columns("notifications")}

    # 1. retry_count 컬럼 추가
    if "retry_count" not in existing:
        with op.batch_alter_table("notifications") as batch_op:
            batch_op.add_column(
                sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0")
            )

    # 2. notification_type: ENUM -> VARCHAR(50)
    op.execute("ALTER TABLE notifications MODIFY COLUMN notification_type VARCHAR(50) NOT NULL")

    # 3. status: ENUM -> VARCHAR(20)
    op.execute("ALTER TABLE notifications MODIFY COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending'")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("notifications"):
        return

    # status: VARCHAR -> ENUM
    op.execute(
        "ALTER TABLE notifications MODIFY COLUMN status "
        "ENUM('pending','sent','delivered','failed','read') NOT NULL DEFAULT 'pending'"
    )

    # notification_type: VARCHAR -> ENUM
    op.execute("DELETE FROM notifications WHERE notification_type IN ('offer_submitted', 'meeting_confirmed')")
    op.execute(
        "ALTER TABLE notifications MODIFY COLUMN notification_type "
        "ENUM('proposal_new','proposal_matched','proposal_cancelled',"
        "'offer_new','offer_accepted','offer_rejected',"
        "'mission_started','mission_completed',"
        "'payment_completed','payment_failed',"
        "'system_announcement','custom') NOT NULL"
    )

    existing = {col["name"] for col in inspector.get_columns("notifications")}
    if "retry_count" in existing:
        with op.batch_alter_table("notifications") as batch_op:
            batch_op.drop_column("retry_count")
