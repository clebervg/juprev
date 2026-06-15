"""Consulta o salário mínimo vigente para uma data específica."""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salario_minimo import SalarioMinimo

logger = logging.getLogger(__name__)

# Fallback caso a tabela ainda não tenha sido populada
_FALLBACK = Decimal("1518.00")


async def salario_minimo_para_data(data: date, db: AsyncSession) -> Decimal:
    """Retorna o salário mínimo vigente na data informada."""
    result = await db.execute(
        select(SalarioMinimo.valor)
        .where(SalarioMinimo.vigencia_inicio <= data)
        .order_by(SalarioMinimo.vigencia_inicio.desc())
        .limit(1)
    )
    valor = result.scalar_one_or_none()
    if valor is None:
        logger.warning("Salário mínimo não encontrado para %s, usando fallback.", data)
        return _FALLBACK
    return Decimal(str(valor))
