"""Cálculo de prazos processuais em dias úteis forenses."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from app.core.logging import get_logger

logger = get_logger(__name__)

# Recesso forense nacional (STJ/TRF) — 20/12 a 06/01 de cada ano.
_RECESSO_INICIO_MES_DIA = (12, 20)
_RECESSO_FIM_MES_DIA = (1, 6)

# Feriados nacionais fixos (mês, dia).
_FERIADOS_FIXOS: set[tuple[int, int]] = {
    (1, 1),   # Confraternização Universal
    (4, 21),  # Tiradentes
    (5, 1),   # Dia do Trabalho
    (9, 7),   # Independência
    (10, 12), # Nossa Senhora Aparecida
    (11, 2),  # Finados
    (11, 15), # Proclamação da República
    (11, 20), # Consciência Negra
    (12, 25), # Natal
}


def _eh_feriado_fixo(d: date) -> bool:
    return (d.month, d.day) in _FERIADOS_FIXOS


def _em_recesso(d: date) -> bool:
    """Verifica se a data está dentro do recesso forense de fim de ano."""
    inicio_mes, inicio_dia = _RECESSO_INICIO_MES_DIA
    fim_mes, fim_dia = _RECESSO_FIM_MES_DIA

    # Recesso cruza o ano: 20/12/ano até 06/01/ano+1
    inicio = date(d.year, inicio_mes, inicio_dia)
    if d >= inicio:
        fim = date(d.year + 1, fim_mes, fim_dia)
        return d <= fim

    # Início do ano: ainda pode estar no recesso do ano anterior
    fim = date(d.year, fim_mes, fim_dia)
    return d <= fim


def eh_dia_util_forense(d: date) -> bool:
    """Retorna True se a data é um dia útil forense (seg-sex, sem feriado, sem recesso)."""
    if d.weekday() >= 5:  # sábado=5, domingo=6
        return False
    if _eh_feriado_fixo(d):
        return False
    if _em_recesso(d):
        return False
    return True


def calcular_vencimento(data_inicio: date, dias_uteis: int) -> date:
    """Conta `dias_uteis` dias úteis forenses a partir de `data_inicio` (exclusive)."""
    atual = data_inicio
    contados = 0
    while contados < dias_uteis:
        atual += timedelta(days=1)
        if eh_dia_util_forense(atual):
            contados += 1
    return atual


def calcular_dias_uteis_entre(inicio: date, fim: date) -> int:
    """Conta quantos dias úteis forenses existem entre duas datas (exclusive início, inclusive fim)."""
    contados = 0
    atual = inicio
    while atual < fim:
        atual += timedelta(days=1)
        if eh_dia_util_forense(atual):
            contados += 1
    return contados


# Mapeamento tipo_movimentacao → (tipo_prazo, dias_uteis_padrão).
_PRAZOS_POR_TIPO: dict[str, tuple[str, int]] = {
    "INTIMACAO":  ("MANIFESTACAO", 15),
    "SENTENCA":   ("RECURSO", 15),
    "DESPACHO":   ("MANIFESTACAO", 5),
    "ACORDAO":    ("RECURSO", 15),
}


def prazo_para_movimentacao(tipo_movimentacao: str) -> tuple[str, int] | None:
    """Retorna (tipo_prazo, dias_uteis) para o tipo de movimentação, ou None se não aplicável."""
    return _PRAZOS_POR_TIPO.get(tipo_movimentacao)
