from logging.config import fileConfig
import os
import re
from dotenv import load_dotenv

load_dotenv()  # load env variables before importing from app
from sqlalchemy import create_engine, engine_from_config
from sqlalchemy import pool

from alembic import context

from app.models.models import Base

target_metadata = Base.metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# config.set_main_option("sqlalchemy.url", os.getenv("DB_URI"))


def get_url():
    # TODO - simplify
    url_tokens = {
        "DB_USERNAME": os.getenv("DB_USERNAME"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        "DEV_PORT": str(os.getenv("DEV_PORT")),
        "TEST_PORT": str(os.getenv("TEST_PORT")),
        "PROD_PORT": str(os.getenv("PROD_PORT")),
        "DB_NAME": os.getenv("DB_NAME"),
        "TEST_HOSTNAME": os.getenv("TEST_HOSTNAME"),
        "PROD_HOSTNAME": os.getenv("PROD_HOSTNAME"),
    }

    url = config.get_main_option("sqlalchemy.url")

    url = re.sub(r"\${(.+?)}", lambda m: url_tokens[m.group(1)], url)

    return url


# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


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
        url=get_url(),
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

    connectable = create_engine(get_url())

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
