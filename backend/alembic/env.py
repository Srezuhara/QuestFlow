"""Alembic environment — pulls DATABASE_URL from app settings and targets
the SQLAlchemy 2.0 declarative Base's metadata for autogenerate.
"""

import asyncio
from logging.config import fileConfig

# Import models so their tables register on Base.metadata before autogenerate
# runs — app.models.__init__ imports every model module.
import app.models  # noqa: F401
from alembic import context
from app.core.config import settings
from app.db.base import Base
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the ini's placeholder URL with the real one from app settings.
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def include_object(
    object: object, name: str | None, type_: str, reflected: bool, compare_to: object
) -> bool:
    """`notes.search_vector` is a hand-written `GENERATED ALWAYS AS ... STORED`
    column (see the migration that adds it) — autogenerate can't produce that
    DDL and, worse, will try to ALTER/DROP it on every subsequent run if it's
    left in scope for comparison. Exclude it here so `alembic revision
    --autogenerate` never touches it.
    """
    if type_ == "column" and name == "search_vector":
        return False
    return not (type_ == "index" and name == "ix_notes_search_vector")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emits SQL, no DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=target_metadata, include_object=include_object
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
