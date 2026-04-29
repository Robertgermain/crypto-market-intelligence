import sys
import os
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context

# -------------------------------------------------------------------
# Add backend root to PYTHONPATH so "app" can be imported
# -------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

# -------------------------------------------------------------------
# Import your app config + Base
# -------------------------------------------------------------------
from app.core.config import settings
from app.core.database import Base

# -------------------------------------------------------------------
# Alembic Config object
# -------------------------------------------------------------------
config = context.config

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -------------------------------------------------------------------
# THIS is what enables autogenerate
# -------------------------------------------------------------------
target_metadata = Base.metadata


# -------------------------------------------------------------------
# OFFLINE MODE
# -------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""

    url = settings.DATABASE_URL

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# -------------------------------------------------------------------
# ONLINE MODE
# -------------------------------------------------------------------
def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    connectable = create_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # detects column type changes
        )

        with context.begin_transaction():
            context.run_migrations()


# -------------------------------------------------------------------
# ENTRYPOINT
# -------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()