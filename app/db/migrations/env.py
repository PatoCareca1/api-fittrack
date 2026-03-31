"""Alembic environment configuration for async migrations.

The database URL is always sourced from ``app.core.config.settings``
so that migrations use the same connection string as the application.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.database import Base

# Ensure every ORM model is imported so Base.metadata is fully populated.
import app.models.orm.user  # noqa: F401
import app.models.orm.analysis  # noqa: F401

# Alembic Config object — gives access to values in alembic.ini.
config = context.config

# Interpret the alembic.ini logging configuration.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the sqlalchemy.url from settings (never from alembic.ini).
config.set_main_option("sqlalchemy.url", settings.database_url)

# MetaData object for 'autogenerate' support.
target_metadata = Base.metadata


# ── Offline (SQL-script) mode ────────────────────────────────────────
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL statements without connecting to the database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online (async) mode ──────────────────────────────────────────────
def do_run_migrations(connection) -> None:
    """Execute migrations within an existing connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations inside a connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    asyncio.run(run_async_migrations())


# ── Entrypoint ───────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
