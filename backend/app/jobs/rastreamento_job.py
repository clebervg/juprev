"""Job periódico de rastreamento de processos — roda a cada hora via APScheduler."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.services.rastreamento_service import rastrear_todos

logger = get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _executar_rastreamento() -> None:
    logger.info("Iniciando job de rastreamento de processos")
    async with AsyncSessionLocal() as db:
        try:
            stats = await rastrear_todos(db)
            total = sum(stats.values())
            logger.info("Rastreamento concluído: %d novas movimentações — %s", total, stats)
        except Exception:
            logger.exception("Erro no job de rastreamento")
            await db.rollback()


def iniciar_scheduler() -> None:
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _executar_rastreamento,
        trigger=IntervalTrigger(hours=1),
        id="rastreamento_processos",
        name="Rastreamento automático de processos",
        replace_existing=True,
        misfire_grace_time=300,
    )
    _scheduler.start()
    logger.info("Scheduler de rastreamento iniciado — intervalo: 1h")


def parar_scheduler() -> None:
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler de rastreamento encerrado")
