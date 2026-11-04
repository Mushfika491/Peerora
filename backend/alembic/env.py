"""Alembic environment: tells Alembic which database and which tables to use."""

from logging.config import fileConfig

from alembic import context

from peerora import models  # noqa: F401  (importing it registers the Tutor table)
from peerora.database import Base, get_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The table definitions Alembic compares against the database.
target_metadata = Base.metadata

# Offline mode (used for the SQL preview) never connects, so it needs no
# DATABASE_URL and no credentials. It only has to know the SQL dialect.
OFFLINE_DIALECT_URL = "postgresql+psycopg://"


def run_migrations_offline() -> None:
    """Print the SQL instead of running it (alembic upgrade head --sql)."""
    context.configure(
        url=OFFLINE_DIALECT_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the real database (DATABASE_URL) and run the migrations."""
    with get_engine().connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()