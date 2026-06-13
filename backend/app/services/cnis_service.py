import hashlib
import logging
import uuid
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cnis import CNIS, CNISPeriodoContribuicao, CNISRemuneracao, CalculoRMI, SimulacaoCenario
from app.repositories.cnis_repository import CNISRepository, CalculoRMIRepository, SimulacaoRepository
from app.schemas.cnis import (
    CalculoRMIRequest,
    CNISCreate,
    SimulacaoRequest,
)
from app.services.calculo_previdenciario import (
    VERSAO_CALCULO,
    RequisitosBeneficio,
    ResultadoCalculo,
    _teto_para_ano,
    analisar_inconsistencias,
    calcular_rmi,
)
from app.services.indices_service import aplicar_correcao_remuneracoes

logger = logging.getLogger(__name__)


def _hash_conteudo(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()


async def criar_cnis(
    data: CNISCreate,
    tenant_id: uuid.UUID,
    db: AsyncSession,
    conteudo_arquivo: bytes | None = None,
) -> CNIS:
    repo = CNISRepository(db)

    if conteudo_arquivo:
        arquivo_hash = _hash_conteudo(conteudo_arquivo)
        if await repo.hash_existe(arquivo_hash, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este arquivo CNIS já foi importado anteriormente.",
            )
    else:
        arquivo_hash = None

    cnis = await repo.create(
        tenant_id=tenant_id,
        cliente_id=data.cliente_id,
        nome_segurado=data.nome_segurado,
        cpf=data.cpf,
        nis=data.nis,
        data_nascimento=data.data_nascimento,
        arquivo_original_nome=data.arquivo_original_nome,
        arquivo_original_hash=arquivo_hash,
        status_processamento="pendente",
    )
    await db.commit()
    await db.refresh(cnis)
    return cnis


async def listar_cnis(
    tenant_id: uuid.UUID,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    repo = CNISRepository(db)
    items, total = await repo.get_by_tenant(tenant_id, skip, limit)
    return {
        "items": [
            {
                "id": str(c.id),
                "cliente_id": str(c.cliente_id),
                # LGPD: não expor nome completo nem CPF na listagem
                "nis": c.nis,
                "periodo_inicial_cn": c.periodo_inicial_cn,
                "periodo_final_cn": c.periodo_final_cn,
                "tempo_contribuicao_anos": c.tempo_contribuicao_anos,
                "total_contribuicoes": c.total_contribuicoes,
                "status_processamento": c.status_processamento,
                "created_at": c.created_at,
            }
            for c in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


async def obter_cnis(
    cnis_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession
) -> CNIS:
    repo = CNISRepository(db)
    cnis = await repo.get_by_id_and_tenant(cnis_id, tenant_id)
    if not cnis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CNIS não encontrado.")
    return cnis


async def deletar_cnis(
    cnis_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession
) -> None:
    repo = CNISRepository(db)
    cnis = await repo.get_by_id_and_tenant(cnis_id, tenant_id)
    if not cnis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CNIS não encontrado.")
    await db.delete(cnis)
    await db.commit()


async def executar_calculo_rmi(
    data: CalculoRMIRequest,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
    genero: str = "masculino",
    data_nascimento: date | None = None,
    tempo_especial_dias: int = 0,
    grau_deficiencia: str | None = None,
) -> CalculoRMI:
    cnis_repo = CNISRepository(db)
    cnis = await cnis_repo.get_by_id_and_tenant(data.cnis_id, tenant_id)
    if not cnis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CNIS não encontrado.")

    remuneracoes = await cnis_repo.get_remuneracoes(data.cnis_id, tenant_id)
    if not remuneracoes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CNIS sem remunerações cadastradas. Cadastre remunerações manualmente ou importe via CSV na aba 'Remunerações' antes de calcular.",
        )

    # Aplica correção monetária (INPC) nos salários históricos antes de calcular o SB
    await aplicar_correcao_remuneracoes(db, remuneracoes, data.data_der)

    dn = data_nascimento or cnis.data_nascimento
    tc_dias = cnis.tempo_contribuicao_total_dias or 0

    req = RequisitosBeneficio(
        tipo_beneficio=data.tipo_beneficio,
        data_der=data.data_der,
        data_nascimento=dn,
        genero=genero,
        tempo_contribuicao_dias=tc_dias,
        tempo_especial_dias=tempo_especial_dias,
        grau_deficiencia=grau_deficiencia,
    )

    teto = Decimal(str(_teto_para_ano(data.data_der.year)))
    resultado: ResultadoCalculo = calcular_rmi(remuneracoes, req, teto_na_der=teto)

    rmi_anterior = None
    diferenca = None
    if resultado.detalhamento.get("rmi_anterior"):
        rmi_anterior = Decimal(str(resultado.detalhamento["rmi_anterior"]))
        diferenca = resultado.rmi_final - rmi_anterior

    calculo_repo = CalculoRMIRepository(db)
    calculo = await calculo_repo.create(
        tenant_id=tenant_id,
        cnis_id=data.cnis_id,
        cliente_id=cnis.cliente_id,
        calculado_por=user_id,
        nome_calculo=data.nome_calculo,
        tipo_beneficio=data.tipo_beneficio,
        regra_aplicada=data.regra_aplicada or resultado.regra_aplicada,
        data_der=data.data_der,
        idade_na_der=req.idade_na_der,
        tempo_contribuicao_na_der=req.tempo_contribuicao_anos,
        salario_beneficio=resultado.salario_beneficio,
        coeficiente_calculo=resultado.coeficiente,
        fator_previdenciario=resultado.fator_previdenciario,
        fator_acumulador=resultado.fator_acumulador,
        rmi_calculada=resultado.rmi_calculada,
        rmi_teto=teto,
        rmi_final=resultado.rmi_final,
        detalhamento_calculo=resultado.detalhamento,
        requisitos_atendidos=resultado.requisitos_atendidos,
        rmi_regra_anterior=rmi_anterior,
        diferenca_reforma=diferenca,
        calculo_valido=resultado.valido,
        alertas=resultado.alertas or None,
        erros=resultado.erros or None,
        versao_calculo=VERSAO_CALCULO,
    )
    await db.commit()
    await db.refresh(calculo)

    logger.info(
        "Cálculo RMI executado — tenant=%s tipo=%s rmi=R$%s valido=%s",
        tenant_id, data.tipo_beneficio, resultado.rmi_final, resultado.valido,
    )
    return calculo


async def obter_calculos_cnis(
    cnis_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession
) -> list[CalculoRMI]:
    cnis_repo = CNISRepository(db)
    if not await cnis_repo.get_by_id_and_tenant(cnis_id, tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CNIS não encontrado.")

    calculo_repo = CalculoRMIRepository(db)
    return await calculo_repo.get_by_cnis(cnis_id, tenant_id)


async def executar_simulacao(
    data: SimulacaoRequest,
    tenant_id: uuid.UUID,
    db: AsyncSession,
    genero: str = "masculino",
) -> SimulacaoCenario:
    cnis_repo = CNISRepository(db)
    cnis = await cnis_repo.get_by_id_and_tenant(data.cnis_id, tenant_id)
    if not cnis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CNIS não encontrado.")

    hoje = date.today()
    anos_futuros = (data.data_simulacao_futura - hoje).days / 365.25
    if anos_futuros < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data de simulação deve ser futura.",
        )

    # Projeta tempo de contribuição
    tc_dias_atual = cnis.tempo_contribuicao_total_dias or 0
    tc_dias_projetado = tc_dias_atual + int(anos_futuros * 365)
    tc_anos_projetado = Decimal(str(tc_dias_projetado / 365.25)).quantize(Decimal("0.01"))

    # Projeta idade
    delta_nascimento = data.data_simulacao_futura - cnis.data_nascimento
    idade_futura = int(delta_nascimento.days / 365.25)

    # Projeta salário de benefício com crescimento
    sb_atual = cnis.media_salarios_contribuicao or Decimal("0")
    taxa_cresc = data.taxa_crescimento_salario
    sb_projetado = sb_atual * (1 + taxa_cresc) ** Decimal(str(anos_futuros))
    sb_projetado = sb_projetado.quantize(Decimal("0.01"))

    # RMI projetada (usa coeficiente por tempo de contribuição)
    from app.services.calculo_previdenciario import calcular_coeficiente
    coef = calcular_coeficiente("aposentadoria_tempo_contribuicao", tc_anos_projetado, genero)
    rmi_projetada = (sb_projetado * coef).quantize(Decimal("0.01"))

    # Traz a valor presente
    taxa_inf = data.taxa_inflacao_anual
    rmi_valor_atual = (rmi_projetada / (1 + taxa_inf) ** Decimal(str(anos_futuros))).quantize(
        Decimal("0.01")
    )

    sim_repo = SimulacaoRepository(db)
    simulacao = await sim_repo.create(
        cnis_id=data.cnis_id,
        nome_simulacao=data.nome_simulacao,
        data_simulacao_futura=data.data_simulacao_futura,
        taxa_crescimento_salario=data.taxa_crescimento_salario,
        taxa_inflacao_anual=data.taxa_inflacao_anual,
        idade_na_data=idade_futura,
        tempo_contribuicao_projetado=tc_anos_projetado,
        salario_beneficio_projetado=sb_projetado,
        rmi_projetada=rmi_projetada,
        rmi_valor_atual=rmi_valor_atual,
    )
    await db.commit()
    await db.refresh(simulacao)
    return simulacao


async def obter_analise_inconsistencias(
    cnis_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession
) -> dict:
    cnis_repo = CNISRepository(db)
    cnis = await cnis_repo.get_by_id_and_tenant(cnis_id, tenant_id)
    if not cnis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CNIS não encontrado.")

    remuneracoes = await cnis_repo.get_remuneracoes(cnis_id, tenant_id)
    periodos = cnis.periodos_contribuicao

    inconsistencias = analisar_inconsistencias(remuneracoes, periodos)

    # Períodos sobrepostos (para o schema de resposta)
    periodos_sobrepostos = [
        {"tipo": i.tipo, "descricao": i.descricao, "periodo": i.periodo_afetado}
        for i in inconsistencias if i.tipo == "periodos_sobrepostos"
    ]

    # Salários suspeitos
    salarios_suspeitos = [
        {"tipo": i.tipo, "descricao": i.descricao, "periodo": i.periodo_afetado}
        for i in inconsistencias if i.tipo in ("salario_zerado", "abaixo_salario_minimo")
    ]

    return {
        "cnis_id": cnis_id,
        "total_inconsistencias": len(inconsistencias),
        "inconsistencias": [
            {
                "tipo": i.tipo,
                "descricao": i.descricao,
                "periodo_afetado": i.periodo_afetado,
                "impacto_financeiro": i.impacto_financeiro,
                "recomendacao": i.recomendacao,
            }
            for i in inconsistencias
        ],
        "periodos_sobrepostos": periodos_sobrepostos,
        "salarios_suspeitos": salarios_suspeitos,
        "periodos_sem_remuneracao": [],
    }
