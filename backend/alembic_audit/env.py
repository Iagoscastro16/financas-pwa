import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv

# Make `app` importable regardless of the cwd alembic was invoked from.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load backend/.env the same way app/config.py does, before app.audit_database
# reads AUDIT_DATABASE_URL from the environment.
load_dotenv()

from app.audit_database import AuditBase, audit_engine  # noqa: E402
from app.models import log_auditoria  # noqa: E402,F401  (registers LogAuditoria on AuditBase.metadata)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Reuse the app's own engine/metadata instead of duplicating connection
# string logic here (see app/audit_database.py for the actual
# AUDIT_DATABASE_URL resolution + defaults).
target_metadata = AuditBase.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=audit_engine.url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    with audit_engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()