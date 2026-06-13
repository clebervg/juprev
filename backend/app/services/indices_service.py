"""
Serviço de correção monetária.

Carrega os índices INPC da tabela indices_correcao e calcula
o fator de atualização para cada competência até a DER.

Uso no cálculo:
    fatores = await carregar_fatores_correcao(db, data_der)
    salario_corrigido = salario_original * fatores.get(competencia, Decimal("1"))
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.indices import IndiceCorrecao

logger = logging.getLogger(__name__)

# Fonte padrão usada pelo INSS para correção de benefícios
FONTE_PADRAO = "INPC"


async def carregar_fatores_correcao(
    db: AsyncSession,
    data_der: date,
    fonte: str = FONTE_PADRAO,
) -> dict[date, Decimal]:
    """
    Retorna um dict {competencia: fator_correcao} onde:
        fator_correcao = acumulado_der / acumulado_competencia

    Salários anteriores à DER devem ser multiplicados pelo fator correspondente.
    Competências sem índice cadastrado retornam fator 1 (sem correção).
    """
    competencia_der = date(data_der.year, data_der.month, 1)

    q = (
        select(IndiceCorrecao)
        .where(
            IndiceCorrecao.fonte == fonte,
            IndiceCorrecao.competencia <= competencia_der,
        )
        .order_by(IndiceCorrecao.competencia)
    )
    rows = list((await db.execute(q)).scalars().all())

    if not rows:
        logger.warning("Nenhum índice %s encontrado até %s", fonte, competencia_der)
        return {}

    # Acumulado na DER (último registro <= DER)
    acumulado_der = next(
        (r.indice_acumulado for r in reversed(rows) if r.competencia <= competencia_der),
        Decimal("1"),
    )

    fatores: dict[date, Decimal] = {}
    for row in rows:
        if row.indice_acumulado > 0:
            fator = (acumulado_der / row.indice_acumulado).quantize(
                Decimal("0.000001"), rounding=ROUND_HALF_UP
            )
        else:
            fator = Decimal("1")
        fatores[row.competencia] = fator

    return fatores


async def aplicar_correcao_remuneracoes(
    db: AsyncSession,
    remuneracoes: list,
    data_der: date,
    fonte: str = FONTE_PADRAO,
) -> list:
    """
    Preenche `salario_contribuicao_corrigido` em cada remuneração usando os índices do banco.
    Modifica a lista in-place e retorna ela.
    """
    fatores = await carregar_fatores_correcao(db, data_der, fonte)

    for rem in remuneracoes:
        competencia = date(rem.mes_referencia.year, rem.mes_referencia.month, 1)
        fator = fatores.get(competencia, Decimal("1"))
        corrigido = (rem.salario_contribuicao * fator).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        rem.salario_contribuicao_corrigido = corrigido

    return remuneracoes


async def obter_indice(
    db: AsyncSession,
    competencia: date,
    fonte: str = FONTE_PADRAO,
) -> IndiceCorrecao | None:
    q = select(IndiceCorrecao).where(
        IndiceCorrecao.competencia == date(competencia.year, competencia.month, 1),
        IndiceCorrecao.fonte == fonte,
    )
    return (await db.execute(q)).scalar_one_or_none()


async def listar_indices(
    db: AsyncSession,
    fonte: str = FONTE_PADRAO,
    ano: int | None = None,
) -> list[IndiceCorrecao]:
    q = select(IndiceCorrecao).where(IndiceCorrecao.fonte == fonte)
    if ano:
        q = q.where(IndiceCorrecao.competencia.between(date(ano, 1, 1), date(ano, 12, 31)))
    q = q.order_by(IndiceCorrecao.competencia)
    return list((await db.execute(q)).scalars().all())
