import os

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from app.models.model import User
from app.models.email_agent import EmailCampaign
from app.models.contacts import Contacts
from app.models.appointment_setter import AppointmentSetter
from app.models.phone_agent import PhoneCampaign
from app.models.social_media_integrations import Instagram
from app.models.account_agent import AccountChatHistory
from app.models.seo_agent import SeoChatHistory
from app.models.coo_agent import CooChatHistory
from app.models.hr_agent import HrChatHistory
from app.models.content_creation_agent import ContentCreationChatHistory

from dotenv import load_dotenv

load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

config.get_main_option("sqlalchemy.url", os.getenv('SQLALCHEMY_DATABASE_URL'))

config.set_main_option("sqlalchemy.url", os.getenv('SQLALCHEMY_DATABASE_URL'))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = [User.metadata]

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
    url = config.get_main_option("sqlalchemy.url", os.getenv('SQLALCHEMY_DATABASE_URL'))
    context.configure(
        url=url,
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
