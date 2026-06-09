"""Remove missions and introduce proofs.

Revision ID: 0006_remove_mission_status
Revises: 0005_create_notifications_table
Create Date: 2026-06-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0006_remove_mission_status"
down_revision = "0005_create_notifications_table"
branch_labels = None
depends_on = None


PROPOSAL_TIMESTAMP_COLUMNS = (
    "matched_at",
    "delivery_reported_at",
    "received_confirmed_at",
    "settled_at",
    "disputed_at",
    "refunded_at",
)
OFFER_TIMESTAMP_COLUMNS = (
    "accepted_at",
    "delivery_completed_at",
    "receipt_confirmed_at",
    "settled_at",
    "disputed_at",
    "refunded_at",
)


def upgrade() -> None:
    bind = op.get_bind()
    _create_proofs_table(bind)
    _add_timestamp_columns(bind, "proposals", PROPOSAL_TIMESTAMP_COLUMNS)
    _add_timestamp_columns(bind, "offers", OFFER_TIMESTAMP_COLUMNS)
    _migrate_mission_data(bind)
    if _has_table(bind, "missions"):
        op.drop_table("missions")


def downgrade() -> None:
    bind = op.get_bind()
    if not _has_table(bind, "missions"):
        op.create_table(
            "missions",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("proposal_id", sa.BigInteger(), nullable=False),
            sa.Column("offer_id", sa.BigInteger(), nullable=False),
            sa.Column("orderer_id", sa.String(length=36), nullable=False),
            sa.Column("runner_id", sa.String(length=36), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="CREATED"),
            sa.Column("delivery_proof_image_url", sa.String(length=500), nullable=True),
            sa.Column("dispute_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("pickup_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("delivery_completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("received_confirmed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("proposal_id", name="uk_proposal_id"),
            sa.UniqueConstraint("offer_id", name="uk_offer_id"),
        )
        op.create_index("ix_missions_id", "missions", ["id"])
        op.create_index("ix_missions_proposal_id", "missions", ["proposal_id"])
        op.create_index("ix_missions_orderer_id", "missions", ["orderer_id"])
        op.create_index("ix_missions_runner_id", "missions", ["runner_id"])

    if _has_table(bind, "proofs"):
        op.drop_table("proofs")

    _drop_timestamp_columns(bind, "offers", OFFER_TIMESTAMP_COLUMNS)
    _drop_timestamp_columns(bind, "proposals", PROPOSAL_TIMESTAMP_COLUMNS)


def _create_proofs_table(bind: sa.engine.Connection) -> None:
    if _has_table(bind, "proofs"):
        return
    op.create_table(
        "proofs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("proposal_id", sa.BigInteger(), nullable=False),
        sa.Column("offer_id", sa.BigInteger(), nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=False),
        sa.Column("proof_type", sa.String(length=30), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_proofs_proposal_id", "proofs", ["proposal_id"])
    op.create_index("ix_proofs_offer_id", "proofs", ["offer_id"])
    op.create_index("ix_proofs_proof_type", "proofs", ["proof_type"])


def _add_timestamp_columns(bind: sa.engine.Connection, table_name: str, column_names: tuple[str, ...]) -> None:
    existing = _column_names(bind, table_name)
    for column_name in column_names:
        if column_name in existing:
            continue
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.add_column(sa.Column(column_name, sa.DateTime(timezone=True), nullable=True))
        existing.add(column_name)


def _drop_timestamp_columns(bind: sa.engine.Connection, table_name: str, column_names: tuple[str, ...]) -> None:
    existing = _column_names(bind, table_name)
    for column_name in reversed(column_names):
        if column_name not in existing:
            continue
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_column(column_name)
        existing.remove(column_name)


def _migrate_mission_data(bind: sa.engine.Connection) -> None:
    if not _has_table(bind, "missions"):
        return
    mission_columns = _column_names(bind, "missions")
    required = {"proposal_id", "offer_id", "created_at"}
    if not required.issubset(mission_columns):
        return

    bind.execute(sa.text("""
        UPDATE proposals
        SET matched_at = (
            SELECT missions.created_at
            FROM missions
            WHERE missions.proposal_id = proposals.id
            LIMIT 1
        )
        WHERE matched_at IS NULL
          AND EXISTS (SELECT 1 FROM missions WHERE missions.proposal_id = proposals.id)
    """))
    bind.execute(sa.text("""
        UPDATE offers
        SET accepted_at = (
            SELECT missions.created_at
            FROM missions
            WHERE missions.offer_id = offers.id
            LIMIT 1
        )
        WHERE accepted_at IS NULL
          AND EXISTS (SELECT 1 FROM missions WHERE missions.offer_id = offers.id)
    """))

    if "delivery_completed_at" in mission_columns:
        bind.execute(sa.text("""
            UPDATE proposals
            SET delivery_reported_at = (
                SELECT missions.delivery_completed_at
                FROM missions
                WHERE missions.proposal_id = proposals.id
                LIMIT 1
            )
            WHERE delivery_reported_at IS NULL
              AND EXISTS (
                  SELECT 1 FROM missions
                  WHERE missions.proposal_id = proposals.id
                    AND missions.delivery_completed_at IS NOT NULL
              )
        """))
        bind.execute(sa.text("""
            UPDATE offers
            SET delivery_completed_at = (
                SELECT missions.delivery_completed_at
                FROM missions
                WHERE missions.offer_id = offers.id
                LIMIT 1
            )
            WHERE delivery_completed_at IS NULL
              AND EXISTS (
                  SELECT 1 FROM missions
                  WHERE missions.offer_id = offers.id
                    AND missions.delivery_completed_at IS NOT NULL
              )
        """))

    if "received_confirmed_at" in mission_columns:
        bind.execute(sa.text("""
            UPDATE proposals
            SET received_confirmed_at = (
                SELECT missions.received_confirmed_at
                FROM missions
                WHERE missions.proposal_id = proposals.id
                LIMIT 1
            )
            WHERE received_confirmed_at IS NULL
              AND EXISTS (
                  SELECT 1 FROM missions
                  WHERE missions.proposal_id = proposals.id
                    AND missions.received_confirmed_at IS NOT NULL
              )
        """))
        bind.execute(sa.text("""
            UPDATE offers
            SET receipt_confirmed_at = (
                SELECT missions.received_confirmed_at
                FROM missions
                WHERE missions.offer_id = offers.id
                LIMIT 1
            )
            WHERE receipt_confirmed_at IS NULL
              AND EXISTS (
                  SELECT 1 FROM missions
                  WHERE missions.offer_id = offers.id
                    AND missions.received_confirmed_at IS NOT NULL
              )
        """))

    if "settled_at" in mission_columns:
        bind.execute(sa.text("""
            UPDATE proposals
            SET settled_at = (
                SELECT missions.settled_at
                FROM missions
                WHERE missions.proposal_id = proposals.id
                LIMIT 1
            )
            WHERE settled_at IS NULL
              AND EXISTS (
                  SELECT 1 FROM missions
                  WHERE missions.proposal_id = proposals.id
                    AND missions.settled_at IS NOT NULL
              )
        """))
        bind.execute(sa.text("""
            UPDATE offers
            SET settled_at = (
                SELECT missions.settled_at
                FROM missions
                WHERE missions.offer_id = offers.id
                LIMIT 1
            )
            WHERE settled_at IS NULL
              AND EXISTS (
                  SELECT 1 FROM missions
                  WHERE missions.offer_id = offers.id
                    AND missions.settled_at IS NOT NULL
              )
        """))

    if {"delivery_proof_image_url", "runner_id"}.issubset(mission_columns):
        bind.execute(sa.text("""
            INSERT INTO proofs (proposal_id, offer_id, actor_id, proof_type, image_url, reason, created_at)
            SELECT proposal_id,
                   offer_id,
                   runner_id,
                   'DELIVERY',
                   delivery_proof_image_url,
                   NULL,
                   COALESCE(delivery_completed_at, created_at)
            FROM missions
            WHERE delivery_proof_image_url IS NOT NULL
        """))

    if {"dispute_reason", "orderer_id", "updated_at"}.issubset(mission_columns):
        bind.execute(sa.text("""
            INSERT INTO proofs (proposal_id, offer_id, actor_id, proof_type, image_url, reason, created_at)
            SELECT proposal_id,
                   offer_id,
                   orderer_id,
                   'DISPUTE',
                   NULL,
                   dispute_reason,
                   COALESCE(updated_at, created_at)
            FROM missions
            WHERE dispute_reason IS NOT NULL
        """))


def _has_table(bind: sa.engine.Connection, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name)


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    if not _has_table(bind, table_name):
        return set()
    return {column["name"] for column in sa.inspect(bind).get_columns(table_name)}
