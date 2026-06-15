from __future__ import annotations

import io
import logging
import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status

logger = logging.getLogger(__name__)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.cnis import (
    AnaliseInconsistenciasResponse,
    CalculoRMIRequest,
    CalculoRMIResponse,
    CNISCreate,
    CNISResponse,
    SimulacaoRequest,
    SimulacaoResponse,
)
from app.services import cnis_service, remuneracoes_service

router = APIRouter(prefix="/cnis", tags=["cnis"])

# ─── Schemas locais para remunerações ────────────────────────────────────────

TipoRemuneracao = Literal[
    "salario", "13o_salario", "ferias", "rescisao",
    "adicional_noturno", "hora_extra", "comissao", "gratificacao", "outros",
]


class RemuneracaoCreate(BaseModel):
    """Payload para cadastro manual de uma remuneração."""

    # Qualquer dia do mês — normalizado para dia 1 no service
    competencia: date
    salario_contribuicao: Decimal = Field(..., ge=0, description="Salário de contribuição bruto")
    tipo_remuneracao: TipoRemuneracao = "salario"
    contribuiu_inss: bool = True


class RemuneracaoResponse(BaseModel):
    """Representação de resposta de uma remuneração."""

    id: uuid.UUID
    cnis_id: uuid.UUID
    mes_referencia: date
    ano: int
    mes: int
    salario_contribuicao: Decimal
    salario_contribuicao_corrigido: Decimal | None
    teto_inss: Decimal | None
    tipo_remuneracao: str | None
    contribuiu_inss: bool
    salario_valido: bool
    acima_teto: bool
    abaixo_minimo: bool

    model_config = {"from_attributes": True}


class RemuneracoesListResponse(BaseModel):
    """Resposta paginada de remunerações."""

    items: list[RemuneracaoResponse]
    total: int
    skip: int
    limit: int

    model_config = {"from_attributes": True}


@router.post("", response_model=CNISResponse, status_code=status.HTTP_201_CREATED)
async def criar_cnis(
    body: CNISCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await cnis_service.criar_cnis(body, current_user.tenant_id, db)


@router.get("", response_model=dict)
async def listar_cnis(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await cnis_service.listar_cnis(current_user.tenant_id, db, skip, limit)


@router.get("/{cnis_id}", response_model=CNISResponse)
async def obter_cnis(
    cnis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await cnis_service.obter_cnis(cnis_id, current_user.tenant_id, db)


@router.delete("/{cnis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_cnis(
    cnis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await cnis_service.deletar_cnis(cnis_id, current_user.tenant_id, db)


# ─── Cálculo RMI ─────────────────────────────────────────────────────────────

@router.post(
    "/{cnis_id}/calculos",
    response_model=CalculoRMIResponse,
    status_code=status.HTTP_201_CREATED,
)
async def calcular_rmi(
    cnis_id: uuid.UUID,
    body: CalculoRMIRequest,
    genero: str = Query("masculino", pattern="^(masculino|feminino)$"),
    data_nascimento: date | None = Query(None),
    tempo_especial_dias: int = Query(0, ge=0),
    grau_deficiencia: str | None = Query(None, pattern="^(leve|moderada|grave)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Garante que o cnis_id da URL bate com o do body
    body = body.model_copy(update={"cnis_id": cnis_id})
    return await cnis_service.executar_calculo_rmi(
        data=body,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        db=db,
        genero=genero,
        data_nascimento=data_nascimento,
        tempo_especial_dias=tempo_especial_dias,
        grau_deficiencia=grau_deficiencia,
    )


@router.get("/{cnis_id}/calculos", response_model=list[CalculoRMIResponse])
async def listar_calculos(
    cnis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await cnis_service.obter_calculos_cnis(cnis_id, current_user.tenant_id, db)


# ─── Análise de Inconsistências ───────────────────────────────────────────────

@router.get("/{cnis_id}/inconsistencias", response_model=AnaliseInconsistenciasResponse)
async def analisar_inconsistencias(
    cnis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await cnis_service.obter_analise_inconsistencias(
        cnis_id, current_user.tenant_id, db
    )


# ─── Simulações de Cenário ────────────────────────────────────────────────────

@router.post(
    "/{cnis_id}/simulacoes",
    response_model=SimulacaoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def simular_cenario(
    cnis_id: uuid.UUID,
    body: SimulacaoRequest,
    genero: str = Query("masculino", pattern="^(masculino|feminino)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    body = body.model_copy(update={"cnis_id": cnis_id})
    return await cnis_service.executar_simulacao(
        data=body,
        tenant_id=current_user.tenant_id,
        db=db,
        genero=genero,
    )


# ─── Remunerações ─────────────────────────────────────────────────────────────

@router.get(
    "/{cnis_id}/remuneracoes",
    response_model=RemuneracoesListResponse,
    summary="Lista as remunerações de um CNIS",
)
async def listar_remuneracoes(
    cnis_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RemuneracoesListResponse:
    """
    Retorna lista paginada de remunerações do CNIS.

    O campo 'total' indica o número total de registros (sem paginação).
    """
    result = await remuneracoes_service.listar_remuneracoes(
        cnis_id=cnis_id,
        tenant_id=current_user.tenant_id,
        db=db,
        skip=skip,
        limit=limit,
    )
    return RemuneracoesListResponse(
        items=[RemuneracaoResponse.model_validate(r) for r in result["items"]],
        total=result["total"],
        skip=skip,
        limit=limit,
    )


@router.post(
    "/{cnis_id}/remuneracoes",
    response_model=RemuneracaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra uma remuneração manualmente",
)
async def criar_remuneracao(
    cnis_id: uuid.UUID,
    body: RemuneracaoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RemuneracaoResponse:
    """
    Cria uma nova remuneração para o CNIS. Normaliza a competência para o
    primeiro dia do mês e recalcula os totalizadores automaticamente.
    """
    remuneracao = await remuneracoes_service.criar_remuneracao(
        cnis_id=cnis_id,
        tenant_id=current_user.tenant_id,
        db=db,
        competencia=body.competencia,
        salario=body.salario_contribuicao,
        tipo=body.tipo_remuneracao,
        contribuiu_inss=body.contribuiu_inss,
    )
    return RemuneracaoResponse.model_validate(remuneracao)


class RemuneracaoUpdate(BaseModel):
    """Payload para edição de uma remuneração existente."""
    competencia: date | None = None
    salario_contribuicao: Decimal | None = Field(None, ge=0)
    tipo_remuneracao: TipoRemuneracao | None = None
    contribuiu_inss: bool | None = None


@router.patch(
    "/{cnis_id}/remuneracoes/{rem_id}",
    response_model=RemuneracaoResponse,
    summary="Edita uma remuneração",
)
async def editar_remuneracao(
    cnis_id: uuid.UUID,
    rem_id: uuid.UUID,
    body: RemuneracaoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RemuneracaoResponse:
    remuneracao = await remuneracoes_service.editar_remuneracao(
        rem_id=rem_id,
        cnis_id=cnis_id,
        tenant_id=current_user.tenant_id,
        data=body,
        db=db,
    )
    return RemuneracaoResponse.model_validate(remuneracao)


@router.delete(
    "/{cnis_id}/remuneracoes/{rem_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma remuneração",
)
async def deletar_remuneracao(
    cnis_id: uuid.UUID,
    rem_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Exclui a remuneração indicada e recalcula os totalizadores do CNIS.
    """
    await remuneracoes_service.deletar_remuneracao(
        rem_id=rem_id,
        cnis_id=cnis_id,
        tenant_id=current_user.tenant_id,
        db=db,
    )


@router.post(
    "/{cnis_id}/remuneracoes/importar-csv",
    status_code=status.HTTP_200_OK,
    summary="Importa remunerações a partir de arquivo CSV",
)
async def importar_remuneracoes_csv(
    cnis_id: uuid.UUID,
    arquivo: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Importa remunerações a partir de um arquivo CSV com as colunas:
    `competencia` (MM/YYYY ou YYYY-MM) e `salario`.

    A primeira linha é ignorada se contiver o cabeçalho "competencia".

    Retorna resumo com `criadas`, `ignoradas` (duplicatas) e `erros`.
    """
    if arquivo.content_type not in ("text/csv", "text/plain", "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Formato de arquivo não suportado. Envie um arquivo CSV.",
        )

    conteudo_bytes = await arquivo.read()
    try:
        conteudo_texto = conteudo_bytes.decode("utf-8")
    except UnicodeDecodeError:
        conteudo_texto = conteudo_bytes.decode("latin-1")

    linhas_raw = conteudo_texto.splitlines()

    # Remove linhas vazias e possível cabeçalho
    linhas_processadas: list[tuple[str, str]] = []
    for i, linha in enumerate(linhas_raw):
        linha = linha.strip()
        if not linha:
            continue
        # Pula cabeçalho se a primeira coluna contém "competencia" (case-insensitive)
        partes = linha.split(",")
        if i == 0 and "competencia" in partes[0].lower():
            continue
        if len(partes) < 2:
            continue
        linhas_processadas.append((partes[0].strip(), partes[1].strip()))

    resultado = await remuneracoes_service.importar_csv(
        cnis_id=cnis_id,
        tenant_id=current_user.tenant_id,
        db=db,
        linhas=linhas_processadas,
    )
    return {"criadas": resultado["criadas"], "ignoradas": resultado["ignoradas"], "erros": resultado["erros"]}


@router.post(
    "/{cnis_id}/remuneracoes/corrigir",
    status_code=status.HTTP_200_OK,
    summary="Aplica correção monetária INPC em todas as remunerações do CNIS",
)
async def corrigir_remuneracoes_cnis(
    cnis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    cnis = await cnis_service.obter_cnis(cnis_id, current_user.tenant_id, db)
    await remuneracoes_service.corrigir_todas_remuneracoes(cnis_id=cnis.id, db=db)
    return {"ok": True}


@router.post(
    "/{cnis_id}/processar-pdf",
    status_code=status.HTTP_200_OK,
    summary="Processa extrato CNIS em PDF e importa remunerações",
)
async def processar_pdf_cnis(
    cnis_id: uuid.UUID,
    arquivo: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Recebe um arquivo PDF do extrato CNIS emitido pelo INSS, extrai as
    competências e salários de contribuição e os persiste como remunerações.

    Suporta vínculos normais (empregado/servidor) e tabelas consolidadas
    por ano civil (cooperativa). Duplicatas são ignoradas silenciosamente.

    Retorna resumo com ``criadas``, ``ignoradas`` e ``erros``.
    """
    if arquivo.content_type not in (
        "application/pdf",
        "application/octet-stream",
        "binary/octet-stream",
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Formato de arquivo não suportado. Envie um arquivo PDF.",
        )

    conteudo_bytes = await arquivo.read()

    try:
        from app.services.pdf_cnis_parser import parse_pdf_cnis  # noqa: PLC0415
        competencias = parse_pdf_cnis(conteudo_bytes)
    except ImportError as exc:
        logger.error("pdfplumber não instalado: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Parser de PDF não disponível no servidor. Contate o suporte.",
        ) from exc
    except ValueError as exc:
        logger.warning("Erro ao parsear PDF CNIS para cnis_id=%s: %s", cnis_id, exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Não foi possível extrair dados do PDF: {exc}",
        ) from exc

    # Apaga tudo e reimporta (o PDF é a fonte de verdade)
    deletadas = await remuneracoes_service.deletar_todas_remuneracoes(
        cnis_id=cnis_id,
        tenant_id=current_user.tenant_id,
        db=db,
    )

    criadas: int = 0
    erros: list[str] = []

    for competencia, salario in competencias:
        try:
            await remuneracoes_service.criar_remuneracao(
                cnis_id=cnis_id,
                tenant_id=current_user.tenant_id,
                db=db,
                competencia=competencia,
                salario=salario,
                tipo="salario",
                contribuiu_inss=True,
                _aplicar_correcao=False,  # corrige em lote abaixo
            )
            criadas += 1
        except Exception as exc:  # noqa: BLE001
            competencia_fmt = f"{competencia.month:02d}/{competencia.year}"
            logger.warning(
                "Erro ao salvar competência %s do cnis_id=%s: %s",
                competencia_fmt, cnis_id, exc,
            )
            erros.append(f"{competencia_fmt}: {exc}")

    # Aplica correção monetária em lote (1 query para todos os fatores INPC)
    await remuneracoes_service.corrigir_todas_remuneracoes(cnis_id=cnis_id, db=db)

    logger.info(
        "PDF CNIS processado para cnis_id=%s: %d deletadas, %d criadas, %d erros.",
        cnis_id, deletadas, criadas, len(erros),
    )
    return {"deletadas": deletadas, "criadas": criadas, "erros": erros}
