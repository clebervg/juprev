"""
Serviço de gerenciamento de remunerações do CNIS.

Responsável por:
- Listar, criar e deletar remunerações de um CNIS
- Importar remunerações a partir de CSV
- Recalcular os totalizadores do CNIS após cada alteração
"""
from __future__ import annotations

import logging
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cnis import CNIS, CNISRemuneracao
from app.services.calculo_previdenciario import _teto_para_ano

logger = logging.getLogger(__name__)

# Salário mínimo de referência (2024) para verificação abaixo_minimo
SALARIO_MINIMO_2024 = Decimal("1412.00")


# ─── Funções públicas ─────────────────────────────────────────────────────────

async def listar_remuneracoes(
    cnis_id: uuid.UUID,
    tenant_id: uuid.UUID,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> dict:
    """
    Lista as remunerações de um CNIS garantindo que pertence ao tenant.

    Retorna dict com 'items' (lista de CNISRemuneracao) e 'total' (int).
    """
    await _validar_cnis_tenant(cnis_id, tenant_id, db)

    total_result = await db.execute(
        select(func.count()).select_from(CNISRemuneracao).where(
            CNISRemuneracao.cnis_id == cnis_id
        )
    )
    total: int = total_result.scalar_one()

    result = await db.execute(
        select(CNISRemuneracao)
        .where(CNISRemuneracao.cnis_id == cnis_id)
        .order_by(CNISRemuneracao.mes_referencia)
        .offset(skip)
        .limit(limit)
    )
    items = list(result.scalars().all())

    return {"items": items, "total": total}


async def criar_remuneracao(
    cnis_id: uuid.UUID,
    tenant_id: uuid.UUID,
    db: AsyncSession,
    competencia: date,
    salario: Decimal,
    tipo: str = "salario",
    contribuiu_inss: bool = True,
) -> CNISRemuneracao:
    """
    Cria uma nova remuneração para o CNIS informado.

    Valida posse do tenant, unicidade da competência, teto do INSS e
    salário mínimo. Após inserção, recalcula os totalizadores do CNIS.
    """
    cnis = await _validar_cnis_tenant(cnis_id, tenant_id, db)

    # Normaliza para o primeiro dia do mês
    mes_referencia = date(competencia.year, competencia.month, 1)

    # Verifica duplicidade de competência
    existe = await db.execute(
        select(CNISRemuneracao).where(
            CNISRemuneracao.cnis_id == cnis_id,
            CNISRemuneracao.mes_referencia == mes_referencia,
        )
    )
    if existe.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe remuneração cadastrada para a competência "
                   f"{mes_referencia.month:02d}/{mes_referencia.year}.",
        )

    teto = _teto_para_ano(mes_referencia.year)
    acima_teto = salario > teto
    abaixo_minimo = salario < SALARIO_MINIMO_2024

    remuneracao = CNISRemuneracao(
        cnis_id=cnis_id,
        mes_referencia=mes_referencia,
        ano=mes_referencia.year,
        mes=mes_referencia.month,
        salario_contribuicao=salario,
        teto_inss=teto,
        tipo_remuneracao=tipo,
        contribuiu_inss=contribuiu_inss,
        acima_teto=acima_teto,
        abaixo_minimo=abaixo_minimo,
    )

    db.add(remuneracao)
    await db.flush()  # obtém o ID antes de recalcular

    await _recalcular_totalizadores(cnis, db)
    await db.commit()
    await db.refresh(remuneracao)

    logger.info(
        "Remuneração criada | cnis_id=%s | competencia=%s/%s | tenant_id=%s",
        cnis_id, mes_referencia.month, mes_referencia.year, tenant_id,
    )
    return remuneracao


async def importar_csv(
    cnis_id: uuid.UUID,
    tenant_id: uuid.UUID,
    db: AsyncSession,
    linhas: list[tuple[str, str]],
) -> dict:
    """
    Importa remunerações a partir de uma lista de tuplas (competencia_str, salario_str).

    competencia_str aceita os formatos "MM/YYYY" ou "YYYY-MM".
    Retorna dict com 'criadas', 'ignoradas' e 'erros'.
    """
    criadas = 0
    ignoradas = 0
    erros: list[str] = []

    for competencia_str, salario_str in linhas:
        try:
            competencia = _parsear_competencia(competencia_str)
            salario = Decimal(salario_str.replace(",", "."))
            await criar_remuneracao(
                cnis_id=cnis_id,
                tenant_id=tenant_id,
                db=db,
                competencia=competencia,
                salario=salario,
            )
            criadas += 1
        except HTTPException as exc:
            if exc.status_code == status.HTTP_409_CONFLICT:
                ignoradas += 1
            else:
                erros.append(f"{competencia_str}: {exc.detail}")
        except (ValueError, InvalidOperation) as exc:
            erros.append(f"{competencia_str}: formato inválido — {exc}")

    logger.info(
        "Importação CSV finalizada | cnis_id=%s | criadas=%d | ignoradas=%d | erros=%d",
        cnis_id, criadas, ignoradas, len(erros),
    )
    return {"criadas": criadas, "ignoradas": ignoradas, "erros": erros}


async def editar_remuneracao(
    rem_id: uuid.UUID,
    cnis_id: uuid.UUID,
    tenant_id: uuid.UUID,
    data: object,
    db: AsyncSession,
) -> CNISRemuneracao:
    """Atualiza competência, salário ou tipo de uma remuneração e recalcula totalizadores."""
    cnis = await _validar_cnis_tenant(cnis_id, tenant_id, db)

    result = await db.execute(
        select(CNISRemuneracao).where(
            CNISRemuneracao.id == rem_id,
            CNISRemuneracao.cnis_id == cnis_id,
        )
    )
    rem = result.scalars().first()
    if rem is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Remuneração não encontrada.")

    updates = data.model_dump(exclude_none=True)  # type: ignore[union-attr]

    if "competencia" in updates:
        nova_comp: date = updates.pop("competencia")
        rem.mes_referencia = nova_comp.replace(day=1)
        rem.ano = nova_comp.year
        rem.mes = nova_comp.month

    for field, value in updates.items():
        setattr(rem, field, value)

    # Recalcula flags de validação com o novo salário
    if "salario_contribuicao" in updates:
        await _recalcular_totalizadores(cnis, db)

    await db.commit()
    await db.refresh(rem)

    logger.info("Remuneração editada | rem_id=%s | cnis_id=%s", rem_id, cnis_id)
    return rem


async def deletar_remuneracao(
    rem_id: uuid.UUID,
    cnis_id: uuid.UUID,
    tenant_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """
    Exclui uma remuneração e recalcula os totalizadores do CNIS.
    """
    cnis = await _validar_cnis_tenant(cnis_id, tenant_id, db)

    result = await db.execute(
        select(CNISRemuneracao).where(
            CNISRemuneracao.id == rem_id,
            CNISRemuneracao.cnis_id == cnis_id,
        )
    )
    remuneracao = result.scalars().first()
    if remuneracao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remuneração não encontrada.",
        )

    await db.delete(remuneracao)
    await db.flush()

    await _recalcular_totalizadores(cnis, db)
    await db.commit()

    logger.info(
        "Remuneração deletada | rem_id=%s | cnis_id=%s | tenant_id=%s",
        rem_id, cnis_id, tenant_id,
    )


# ─── Funções internas ─────────────────────────────────────────────────────────

async def _validar_cnis_tenant(
    cnis_id: uuid.UUID,
    tenant_id: uuid.UUID,
    db: AsyncSession,
) -> CNIS:
    """
    Verifica que o CNIS existe e pertence ao tenant do usuário autenticado.
    Levanta 404 se não encontrado ou 403 se não pertencer ao tenant.
    """
    result = await db.execute(
        select(CNIS).where(CNIS.id == cnis_id)
    )
    cnis = result.scalars().first()

    if cnis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CNIS não encontrado.",
        )
    if cnis.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a este CNIS.",
        )
    return cnis


async def _recalcular_totalizadores(cnis: CNIS, db: AsyncSession) -> None:
    """
    Recalcula os campos totalizadores do CNIS com base nas remunerações válidas.

    Campos atualizados:
    - total_contribuicoes
    - maior_salario_contribuicao
    - media_salarios_contribuicao
    - tempo_contribuicao_total_dias
    - tempo_contribuicao_anos
    - status_processamento → "concluido"
    """
    result = await db.execute(
        select(CNISRemuneracao).where(
            CNISRemuneracao.cnis_id == cnis.id,
            CNISRemuneracao.salario_valido.is_(True),
        )
    )
    remuneracoes_validas = list(result.scalars().all())

    # Conta meses distintos com contribuição ao INSS
    meses_com_contribuicao: set[date] = {
        r.mes_referencia
        for r in remuneracoes_validas
        if r.contribuiu_inss
    }
    tempo_contribuicao_total_dias = len(meses_com_contribuicao) * 30
    tempo_contribuicao_anos = (
        Decimal(tempo_contribuicao_total_dias) / Decimal("365.25")
    ).quantize(Decimal("0.01"))

    total_contribuicoes = len(meses_com_contribuicao)

    salarios = [r.salario_contribuicao for r in remuneracoes_validas]
    maior_salario = max(salarios, default=Decimal("0.00"))
    media_salarios = (
        sum(salarios) / Decimal(len(salarios))
        if salarios
        else Decimal("0.00")
    ).quantize(Decimal("0.01"))

    cnis.total_contribuicoes = total_contribuicoes
    cnis.maior_salario_contribuicao = maior_salario
    cnis.media_salarios_contribuicao = media_salarios
    cnis.tempo_contribuicao_total_dias = tempo_contribuicao_total_dias
    cnis.tempo_contribuicao_anos = tempo_contribuicao_anos
    cnis.status_processamento = "concluido"

    db.add(cnis)


def _parsear_competencia(competencia_str: str) -> date:
    """
    Converte string de competência nos formatos "MM/YYYY" ou "YYYY-MM" para date.
    Retorna sempre o primeiro dia do mês.

    Levanta ValueError se o formato não for reconhecido.
    """
    competencia_str = competencia_str.strip()
    if "/" in competencia_str:
        parts = competencia_str.split("/")
        if len(parts) != 2:
            raise ValueError(f"Formato esperado MM/YYYY, recebido: '{competencia_str}'")
        mes, ano = int(parts[0]), int(parts[1])
    elif "-" in competencia_str:
        parts = competencia_str.split("-")
        if len(parts) != 2:
            raise ValueError(f"Formato esperado YYYY-MM, recebido: '{competencia_str}'")
        ano, mes = int(parts[0]), int(parts[1])
    else:
        raise ValueError(
            f"Formato de competência não reconhecido: '{competencia_str}'. "
            "Use MM/YYYY ou YYYY-MM."
        )

    if not (1 <= mes <= 12):
        raise ValueError(f"Mês inválido: {mes}. Deve ser entre 1 e 12.")
    if ano < 1900 or ano > 2100:
        raise ValueError(f"Ano inválido: {ano}.")

    return date(ano, mes, 1)
