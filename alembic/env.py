from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from alembic.ddl.mysql import MySQLImpl
from sqlalchemy import Column, MetaData, PrimaryKeyConstraint, String, Table
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base

# Import models so Base.metadata is populated for autogenerate.
from app.models import dispute_evidence, dispute_survey, notification, offer, proposal, settlement, terms, user  # noqa: F401


config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def mysql_version_table_impl(
    self,
    *,
    version_table: str,
    version_table_schema: str | None,
    version_table_pk: bool,
    **kw,
) -> Table:
    """Use staging-compatible width for descriptive Alembic revision IDs."""
    _ = self, kw
    version_table_object = Table(
        version_table,
        MetaData(),
        Column("version_num", String(255), nullable=False),
        schema=version_table_schema,
    )
    if version_table_pk:
        version_table_object.append_constraint(
            PrimaryKeyConstraint("version_num", name=f"{version_table}_pkc")
        )

    return version_table_object


MySQLImpl.version_table_impl = mysql_version_table_impl


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
