from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from alembic.operations import Operations, MigrateOperation

from knotty import model

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = model.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


@Operations.register_operation("create_collation")
class CreateCollationOp(MigrateOperation):
    """Create a COLLATION."""

    def __init__(
        self,
        collation_name: str,
        *,
        schema=None,
        provider: str,
        locale: str,
        deterministic: bool = True,
    ):
        self.collation_name = collation_name
        self.schema = schema
        self.provider = provider
        self.locale = locale
        self.deterministic = deterministic

    @classmethod
    def create_collation(cls, operations, collation_name: str, **kwargs):
        """Issue a "CREATE COLLATION" instruction."""

        op = CreateCollationOp(collation_name, **kwargs)
        return operations.invoke(op)

    def reverse(self):
        return DropCollationOp(
            self.collation_name,
            schema=self.schema,
        )


@Operations.register_operation("drop_collation")
class DropCollationOp(MigrateOperation):
    """Drop a COLLATION."""

    def __init__(self, collation_name: str, *, schema=None):
        self.collation_name = collation_name
        self.schema = schema

    @classmethod
    def drop_collation(cls, operations, collation_name: str, **kwargs):
        """Issue a "DROP COLLATION" instruction."""

        op = DropCollationOp(collation_name, **kwargs)
        return operations.invoke(op)


@Operations.implementation_for(CreateCollationOp)
def create_collation(operations, operation: CreateCollationOp):
    if operation.schema is not None:
        name = f"{operation.schema}.{operation.collation_name}"
    else:
        name = operation.collation_name

    deterministic = "true" if operation.deterministic else "false"

    sql = f"CREATE COLLATION {name} \
           (provider = {operation.provider}, \
           locale = '{operation.locale}', \
           deterministic = {deterministic})"
    operations.execute(sql)


@Operations.implementation_for(DropCollationOp)
def drop_collation(operations, operation: DropCollationOp):
    if operation.schema is not None:
        name = f"{operation.schema}.{operation.collation_name}"
    else:
        name = operation.collation_name

    operations.execute(f"DROP COLLATION {name}")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

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
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
