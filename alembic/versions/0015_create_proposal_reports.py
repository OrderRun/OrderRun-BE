"""Create Proposal report tables and add reported Proposal status.

Revision ID: 0015_create_proposal_reports
Revises: 0014_hard_delete_withdrawn_user_pii
Create Date: 2026-06-22
"""

from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op


revision = "0015_create_proposal_reports"
down_revision = "0014_hard_delete_withdrawn_user_pii"
branch_labels = None
depends_on = None


REASONS = (
    "광고 또는 스팸이에요",
    "욕설이나 혐오 표현이 있어요",
    "거짓 정보 같아요",
    "부적절한 사진이나 내용이에요",
    "기타",
)


def upgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("proposals"):
        op.alter_column(
            "proposals",
            "status",
            existing_type=sa.Enum(
                "HOLDING", "POSTED", "OFFERED", "MATCHED", "ORDER_COMPLETED", "ALL_COMPLETED", "DISPUTED", "RESOLVED", "CANCELLED",
                name="proposalstatus",
            ),
            type_=sa.Enum(
                "HOLDING", "POSTED", "OFFERED", "MATCHED", "ORDER_COMPLETED", "ALL_COMPLETED", "DISPUTED", "RESOLVED", "REPORTED", "CANCELLED",
                name="proposalstatus",
            ),
            existing_nullable=False,
        )

    if not sa.inspect(bind).has_table("proposal_report_reason_questions"):
        op.create_table(
            "proposal_report_reason_questions",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("question_text", sa.String(length=500), nullable=False),
            sa.Column("display_order", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("display_order", name="uk_proposal_report_reason_questions_display_order"),
        )
        op.create_index(
            "idx_proposal_report_reason_questions_lookup",
            "proposal_report_reason_questions",
            ["is_active", "display_order", "id"],
        )
        now = datetime.now(timezone.utc)
        op.bulk_insert(
            sa.table(
                "proposal_report_reason_questions",
                sa.column("question_text", sa.String()),
                sa.column("display_order", sa.Integer()),
                sa.column("is_active", sa.Boolean()),
                sa.column("created_at", sa.DateTime()),
                sa.column("updated_at", sa.DateTime()),
            ),
            [
                {
                    "question_text": reason,
                    "display_order": index,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                }
                for index, reason in enumerate(REASONS, start=1)
            ],
        )

    if not sa.inspect(bind).has_table("proposal_reports"):
        op.create_table(
            "proposal_reports",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("proposal_id", sa.BigInteger(), nullable=False),
            sa.Column("reporter_id", sa.String(length=36), nullable=False),
            sa.Column("reason_question_id", sa.BigInteger(), nullable=False),
            sa.Column("detail_reason", sa.String(length=500), nullable=True),
            sa.Column("status", sa.Enum("PENDING", "ACCEPTED", "REJECTED", name="proposalreportstatus"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("proposal_id", "reporter_id", name="uk_proposal_reports_proposal_reporter"),
        )
        op.create_index("idx_proposal_reports_proposal_status", "proposal_reports", ["proposal_id", "status", "id"])
        op.create_index("idx_proposal_reports_reporter_id", "proposal_reports", ["reporter_id"])
        op.create_index("idx_proposal_reports_status_created", "proposal_reports", ["status", "created_at", "id"])


def downgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("proposal_reports"):
        op.drop_index("idx_proposal_reports_status_created", table_name="proposal_reports")
        op.drop_index("idx_proposal_reports_reporter_id", table_name="proposal_reports")
        op.drop_index("idx_proposal_reports_proposal_status", table_name="proposal_reports")
        op.drop_table("proposal_reports")
    if sa.inspect(bind).has_table("proposal_report_reason_questions"):
        op.drop_index("idx_proposal_report_reason_questions_lookup", table_name="proposal_report_reason_questions")
        op.drop_table("proposal_report_reason_questions")
    if sa.inspect(bind).has_table("proposals"):
        op.alter_column(
            "proposals",
            "status",
            existing_type=sa.Enum(
                "HOLDING", "POSTED", "OFFERED", "MATCHED", "ORDER_COMPLETED", "ALL_COMPLETED", "DISPUTED", "RESOLVED", "REPORTED", "CANCELLED",
                name="proposalstatus",
            ),
            type_=sa.Enum(
                "HOLDING", "POSTED", "OFFERED", "MATCHED", "ORDER_COMPLETED", "ALL_COMPLETED", "DISPUTED", "RESOLVED", "CANCELLED",
                name="proposalstatus",
            ),
            existing_nullable=False,
        )
