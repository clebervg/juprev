"""Orquestra a consulta de tribunais, persistência de movimentações, prazos e alertas."""
from __future__ import annotations

import uuid
from datetime import timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.alerta import AlertaProcessual
from app.models.movimentacao import MovimentacaoProcessual
from app.models.prazo import PrazoProcessual
from app.models.processo import ProcessoJudicial
from app.repositories.movimentacao_repository import MovimentacaoRepository
from app.repositories.processo_repository import ProcessoRepository
from app.services.prazos_service import (
    calcular_dias_uteis_entre,
    calcular_vencimento,
    prazo_para_movimentacao,
)
from app.services.scrapers import (
    STJScraper,
    TRF1Scraper,
    TRF3Scraper,
    TRF4Scraper,
    TNUScraper,
    ScraperBase,
)

logger = get_logger(__name__)

_SCRAPERS: dict[str, type[ScraperBase]] = {
    "TRF1": TRF1Scraper,
    "TRF3": TRF3Scraper,
    "TRF4": TRF4Scraper,
    "TNU": TNUScraper,
    "STJ": STJScraper,
}


async def rastrear_processo(db: AsyncSession, processo: ProcessoJudicial) -> int:
    """
    Consulta o tribunal do processo, persiste novas movimentações, cria prazos e alertas.
    Retorna o número de novas movimentações encontradas.
    """
    scraper_cls = _SCRAPERS.get(processo.tribunal)
    if not scraper_cls:
        logger.warning("Tribunal não suportado: %s", processo.tribunal)
        return 0

    async with scraper_cls() as scraper:
        resultado = await scraper.consultar(processo.numero_cnj)

    if not resultado.sucesso:
        logger.warning(
            "Falha ao consultar tribunal processo=%s erro=%s",
            processo.numero_cnj,
            resultado.erro,
        )
        return 0

    mov_repo = MovimentacaoRepository(db)
    novas = 0

    # Atualiza metadados do processo se o scraper retornou
    if resultado.vara and not processo.vara:
        processo.vara = resultado.vara
    if resultado.classe_processual and not processo.classe_processual:
        processo.classe_processual = resultado.classe_processual

    for mov_scraping in resultado.movimentacoes:
        if await mov_repo.hash_exists(processo.id, mov_scraping.hash_conteudo):
            continue

        movimentacao = MovimentacaoProcessual(
            id=uuid.uuid4(),
            processo_id=processo.id,
            tenant_id=processo.tenant_id,
            data_movimentacao=mov_scraping.data_movimentacao,
            descricao=mov_scraping.descricao,
            tipo=mov_scraping.tipo,
            hash_conteudo=mov_scraping.hash_conteudo,
            origem_tribunal=processo.tribunal,
            documento_url=mov_scraping.documento_url,
        )
        db.add(movimentacao)
        await db.flush()

        _criar_prazo_se_aplicavel(db, processo, movimentacao)
        _criar_alerta(db, processo, movimentacao)
        novas += 1

    if novas:
        logger.info(
            "processo=%s tribunal=%s novas_movimentacoes=%d",
            processo.numero_cnj,
            processo.tribunal,
            novas,
        )

    return novas


def _criar_prazo_se_aplicavel(
    db: AsyncSession,
    processo: ProcessoJudicial,
    movimentacao: MovimentacaoProcessual,
) -> None:
    prazo_info = prazo_para_movimentacao(movimentacao.tipo)
    if not prazo_info:
        return

    tipo_prazo, dias_uteis = prazo_info
    data_inicio = movimentacao.data_movimentacao.astimezone(timezone.utc).date()
    data_vencimento = calcular_vencimento(data_inicio, dias_uteis)
    dias_corridos = (data_vencimento - data_inicio).days

    descricoes = {
        "CONTESTACAO": "Prazo para contestação",
        "RECURSO": "Prazo recursal",
        "CONTRARRAZOES": "Prazo para contrarrazões",
        "MANIFESTACAO": "Prazo para manifestação",
        "CUMPRIMENTO_SENTENCA": "Prazo para cumprimento de sentença",
        "OUTROS": "Prazo processual",
    }

    prazo = PrazoProcessual(
        id=uuid.uuid4(),
        processo_id=processo.id,
        movimentacao_id=movimentacao.id,
        tenant_id=processo.tenant_id,
        tipo_prazo=tipo_prazo,
        descricao=descricoes.get(tipo_prazo, "Prazo processual"),
        dias_corridos=dias_corridos,
        dias_uteis=dias_uteis,
        data_inicio=data_inicio,
        data_vencimento=data_vencimento,
    )
    db.add(prazo)


def _criar_alerta(
    db: AsyncSession,
    processo: ProcessoJudicial,
    movimentacao: MovimentacaoProcessual,
) -> None:
    tipo_alerta_map = {
        "SENTENCA": "SENTENCA",
        "INTIMACAO": "INTIMACAO",
    }
    tipo_alerta = tipo_alerta_map.get(movimentacao.tipo, "NOVA_MOVIMENTACAO")

    mensagem = (
        f"Nova movimentação em {processo.numero_cnj} ({processo.tribunal}): "
        f"{movimentacao.descricao[:200]}"
    )

    alerta = AlertaProcessual(
        id=uuid.uuid4(),
        processo_id=processo.id,
        movimentacao_id=movimentacao.id,
        tenant_id=processo.tenant_id,
        tipo=tipo_alerta,
        mensagem=mensagem,
    )
    db.add(alerta)


async def rastrear_todos(db: AsyncSession) -> dict[str, int]:
    """Rastreia todos os processos monitorados. Retorna estatísticas por tribunal."""
    proc_repo = ProcessoRepository(db)
    processos = await proc_repo.get_monitorados()

    stats: dict[str, int] = {}
    for processo in processos:
        novas = await rastrear_processo(db, processo)
        stats[processo.tribunal] = stats.get(processo.tribunal, 0) + novas

    await db.commit()
    return stats
