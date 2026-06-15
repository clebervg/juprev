import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db.base import Base
from app.models import Client, Dependente, Tenant, User, CNIS, CNISPeriodoContribuicao, CNISRemuneracao, CalculoRMI, SimulacaoCenario, IndiceCorrecao, ProcessoJudicial, MovimentacaoProcessual, PrazoProcessual, AlertaProcessual  # noqa: F401 — registra todos os models
from app.models.salario_minimo import SalarioMinimo  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=_is_sqlite,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.DATABASE_URL)
    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda conn: context.configure(
                connection=conn,
                target_metadata=target_metadata,
                render_as_batch=_is_sqlite,
            )
        )
        async with connection.begin():
            await connection.run_sync(lambda _: context.run_migrations())
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
