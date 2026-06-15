"""
Serviço de parsing do extrato CNIS em PDF emitido pelo INSS.

Suporta dois formatos de vínculo:
  - Empregado/Empregador: pares (competência, remuneração) na página.
  - Cooperativa: tabela "Valores Consolidados por Ano Civil" com colunas mensais.

A deduplicação prioriza valores do vínculo normal sobre a tabela consolidada.
"""
from __future__ import annotations

import logging
import re
from datetime import date
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

# Captura MM/AAAA (não precedido de dígito, para não casar dentro de 01/11/1996)
_PATTERN_COMPETENCIA = re.compile(r'(?<!\d)(\d{2}/\d{4})')

# Captura valor monetário BR: dígitos + separadores de milhar + vírgula decimal
# Ex: 297,25  |  1.920,10  |  13.530,18
# NÃO casa: inteiros isolados como "1", "12" ou CNPJs sem vírgula
_PATTERN_VALOR = re.compile(r'\d[\d.]*,\d+')

# Header que indica início da tabela consolidada
_HEADER_CONSOLIDADO = "valores consolidados por ano civil"

# Nomes dos meses em ordem para mapear colunas
_MESES_NOMES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

# Limites para filtrar valores claramente inválidos
_SALARIO_MAXIMO_PLAUSIVEL = Decimal("999999")
_SALARIO_MINIMO_PLAUSIVEL = Decimal("50")  # nenhum SC válido foi abaixo disso historicamente


def _parse_valor(texto: str) -> Decimal | None:
    """Converte string monetária brasileira ('1.234,56') em Decimal."""
    texto = texto.strip()
    if not texto or texto in ("-", "0", ""):
        return None
    try:
        if "," in texto:
            normalizado = texto.replace(".", "").replace(",", ".")
        else:
            normalizado = texto.replace(",", "")
        valor = Decimal(normalizado)
        if valor < _SALARIO_MINIMO_PLAUSIVEL or valor > _SALARIO_MAXIMO_PLAUSIVEL:
            return None
        return valor
    except InvalidOperation:
        logger.debug("Valor não convertível: %s", texto)
        return None


def _competencia_para_date(competencia: str) -> date | None:
    """Converte 'MM/AAAA' para date(AAAA, MM, 1)."""
    try:
        mm, yyyy = competencia.split("/")
        return date(int(yyyy), int(mm), 1)
    except (ValueError, TypeError):
        return None


def _extrair_vinculo_normal(texto_pagina: str) -> dict[date, Decimal]:
    """
    Extrai pares (competência, salário) de páginas de vínculo normal.

    Estratégia por linha: coleta posições de todas as competências e de todos
    os valores monetários (com vírgula). Para cada competência, associa o
    primeiro valor monetário que aparece depois dela e antes da próxima
    competência. Isso tolera lixo textual entre data e valor (ex: "11/1996 1 297,25").
    """
    resultado: dict[date, Decimal] = {}
    for linha in texto_pagina.splitlines():
        competencias = [(m.start(), m.group(1)) for m in _PATTERN_COMPETENCIA.finditer(linha)]
        valores = [(m.start(), m.group(0)) for m in _PATTERN_VALOR.finditer(linha)]

        if not competencias or not valores:
            continue

        for i, (pos_comp, comp_str) in enumerate(competencias):
            pos_prox = competencias[i + 1][0] if i + 1 < len(competencias) else len(linha)
            candidatos = [v for pos_v, v in valores if pos_comp < pos_v < pos_prox]
            if not candidatos:
                continue
            dt = _competencia_para_date(comp_str)
            if dt is None:
                continue
            valor = _parse_valor(candidatos[0])
            if valor is None:
                continue
            if dt not in resultado:
                resultado[dt] = valor
    return resultado


def _extrair_tabela_consolidada(pagina: object) -> dict[date, Decimal]:
    """
    Extrai competências da tabela "Valores Consolidados por Ano Civil" usando
    extract_tables() do pdfplumber para preservar alinhamento de colunas.

    Células vazias retornam None, evitando erros de posição em linhas esparsas
    (ex: 2019 com apenas Nov-Dez).
    """
    resultado: dict[date, Decimal] = {}

    tabelas = pagina.extract_tables()  # type: ignore[attr-defined]
    for tabela in tabelas:
        if not tabela:
            continue

        # Encontra a linha de cabeçalho que contém nomes de meses
        header_row: list | None = None
        header_idx: int = 0
        for i, row in enumerate(tabela):
            if row and any(
                cell and str(cell).strip().lower()[:3] in _MESES_NOMES
                for cell in row
            ):
                header_row = row
                header_idx = i
                break

        if header_row is None:
            continue

        # Mapeia índice de coluna → número do mês (1-12)
        col_to_mes: dict[int, int] = {}
        for col_idx, cell in enumerate(header_row):
            if not cell:
                continue
            prefixo = str(cell).strip().lower()[:3]
            if prefixo in _MESES_NOMES:
                col_to_mes[col_idx] = _MESES_NOMES.index(prefixo) + 1

        if not col_to_mes:
            continue

        # Processa linhas de dados
        for row in tabela[header_idx + 1:]:
            if not row or not row[0]:
                continue
            ano_str = str(row[0]).strip()
            if not re.match(r'^\d{4}$', ano_str):
                continue
            ano = int(ano_str)

            for col_idx, cell in enumerate(row):
                if col_idx not in col_to_mes or not cell:
                    continue
                valor = _parse_valor(str(cell))
                if valor is None:
                    continue
                mes = col_to_mes[col_idx]
                dt = date(ano, mes, 1)
                if dt not in resultado:
                    resultado[dt] = valor

    return resultado


def parse_pdf_cnis(conteudo_pdf: bytes) -> list[tuple[date, Decimal]]:
    """
    Recebe o conteúdo binário de um PDF de extrato CNIS e retorna uma lista
    de tuplas ``(competencia: date, salario: Decimal)``, sem duplicatas.

    A deduplicação favorece valores de vínculos normais sobre a tabela
    consolidada (a tabela preenche apenas os gaps).

    Args:
        conteudo_pdf: Bytes do arquivo PDF.

    Returns:
        Lista ordenada de (date, Decimal) representando cada competência.

    Raises:
        ImportError: Se a biblioteca pdfplumber não estiver instalada.
        ValueError: Se o PDF não puder ser lido ou não contiver dados válidos.
    """
    try:
        import pdfplumber  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "pdfplumber não está instalado. Execute: pip install pdfplumber>=0.11"
        ) from exc

    import io

    vinculo_normal: dict[date, Decimal] = {}
    consolidado: dict[date, Decimal] = {}

    try:
        with pdfplumber.open(io.BytesIO(conteudo_pdf)) as pdf:
            for num_pagina, pagina in enumerate(pdf.pages, start=1):
                texto = pagina.extract_text() or ""

                # Sempre extrai vínculos individuais (presente em todas as páginas)
                for dt, val in _extrair_vinculo_normal(texto).items():
                    if dt not in vinculo_normal:
                        vinculo_normal[dt] = val

                # Extrai tabela consolidada quando presente (pode coexistir na mesma página)
                if _HEADER_CONSOLIDADO in texto.lower():
                    logger.debug("Página %d: tabela consolidada detectada.", num_pagina)
                    for dt, val in _extrair_tabela_consolidada(pagina).items():
                        if dt not in consolidado:
                            consolidado[dt] = val
    except Exception as exc:
        raise ValueError(f"Erro ao processar PDF CNIS: {exc}") from exc

    # Mescla: vínculo normal tem prioridade; consolidado preenche gaps
    merged: dict[date, Decimal] = {**consolidado, **vinculo_normal}

    if not merged:
        logger.warning("Nenhuma competência extraída do PDF CNIS.")

    return sorted(merged.items(), key=lambda x: x[0])
