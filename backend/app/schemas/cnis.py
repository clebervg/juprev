import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


# ─── Tipos compartilhados ────────────────────────────────────────────────────

TipoBeneficio = Literal[
    "aposentadoria_idade_urbana",
    "aposentadoria_idade_rural",
    "aposentadoria_tempo_contribuicao",
    "aposentadoria_especial_15",
    "aposentadoria_especial_20",
    "aposentadoria_especial_25",
    "aposentadoria_pcd_idade",
    "aposentadoria_pcd_tempo",
    "auxilio_doenca",
    "aposentadoria_invalidez",
    "salario_maternidade",
    "pensao_morte",
]

TipoContribuinte = Literal[
    "empregado", "empregador", "contribuinte_individual",
    "segurado_especial", "facultativo", "estagiario",
    "avulso", "dirigente_sindical",
]


# ─── CNIS ────────────────────────────────────────────────────────────────────

class CNISCreate(BaseModel):
    cliente_id: uuid.UUID
    nome_segurado: str = Field(..., min_length=2, max_length=255)
    cpf: str = Field(..., min_length=11, max_length=11)
    nis: str = Field(..., min_length=11, max_length=11)
    data_nascimento: date
    arquivo_original_nome: str | None = None


class CNISResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    cliente_id: uuid.UUID
    nome_segurado: str
    nis: str
    data_nascimento: date
    periodo_inicial_cn: date | None
    periodo_final_cn: date | None
    tempo_contribuicao_total_dias: int | None
    tempo_contribuicao_anos: Decimal | None
    total_contribuicoes: int | None
    maior_salario_contribuicao: Decimal | None
    media_salarios_contribuicao: Decimal | None
    status_processamento: str
    erros_validacao: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Período de Contribuição ─────────────────────────────────────────────────

class PeriodoContribuicaoCreate(BaseModel):
    cnis_id: uuid.UUID
    cnpj_empregador: str | None = None
    razao_social_empregador: str | None = None
    data_inicio: date
    data_fim: date | None = None
    tipo_contribuinte: TipoContribuinte | None = None
    categoria: str | None = None
    dias_contribuidos: int = Field(..., ge=0)
    indicador_aposentadoria_especial: bool = False
    agente_nocivo: str | None = None
    grau_deficiencia: Literal["leve", "moderada", "grave"] | None = None
    observacoes: str | None = None


class PeriodoContribuicaoResponse(BaseModel):
    id: uuid.UUID
    cnpj_empregador: str | None
    razao_social_empregador: str | None
    data_inicio: date
    data_fim: date | None
    tipo_contribuinte: str | None
    dias_contribuidos: int
    indicador_aposentadoria_especial: bool
    agente_nocivo: str | None
    grau_deficiencia: str | None
    total_remuneracoes: Decimal | None
    quantidade_remuneracoes: int | None
    periodo_valido: bool
    motivo_invalidacao: str | None

    model_config = {"from_attributes": True}


# ─── Remuneração ─────────────────────────────────────────────────────────────

class RemuneracaoResponse(BaseModel):
    id: uuid.UUID
    mes_referencia: date
    ano: int
    mes: int
    salario_contribuicao: Decimal
    salario_contribuicao_corrigido: Decimal | None
    teto_inss: Decimal | None
    contribuiu_inss: bool
    salario_valido: bool
    acima_teto: bool
    abaixo_minimo: bool

    model_config = {"from_attributes": True}


# ─── Cálculo RMI ─────────────────────────────────────────────────────────────

class CalculoRMIRequest(BaseModel):
    cnis_id: uuid.UUID
    tipo_beneficio: TipoBeneficio
    data_der: date = Field(..., description="Data de Entrada do Requerimento (real ou simulada)")
    nome_calculo: str = Field(..., min_length=2, max_length=100)
    regra_aplicada: str | None = None


class CalculoRMIResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    cnis_id: uuid.UUID
    cliente_id: uuid.UUID
    nome_calculo: str
    tipo_beneficio: str
    regra_aplicada: str | None
    data_der: date
    idade_na_der: int
    tempo_contribuicao_na_der: Decimal
    salario_beneficio: Decimal
    coeficiente_calculo: Decimal
    fator_previdenciario: Decimal | None
    fator_acumulador: Decimal | None
    rmi_calculada: Decimal
    rmi_teto: Decimal | None
    rmi_final: Decimal
    detalhamento_calculo: dict
    requisitos_atendidos: dict | None
    rmi_regra_anterior: Decimal | None
    diferenca_reforma: Decimal | None
    calculo_valido: bool
    alertas: list | None
    erros: list | None
    versao_calculo: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Simulação de Cenário ─────────────────────────────────────────────────────

class SimulacaoRequest(BaseModel):
    cnis_id: uuid.UUID
    nome_simulacao: str | None = None
    data_simulacao_futura: date
    taxa_crescimento_salario: Decimal = Field(Decimal("0.03"), ge=0, le=1)
    taxa_inflacao_anual: Decimal = Field(Decimal("0.045"), ge=0, le=1)


class SimulacaoResponse(BaseModel):
    id: uuid.UUID
    cnis_id: uuid.UUID
    nome_simulacao: str | None
    data_simulacao_futura: date
    taxa_crescimento_salario: Decimal | None
    taxa_inflacao_anual: Decimal | None
    idade_na_data: int | None
    tempo_contribuicao_projetado: Decimal | None
    salario_beneficio_projetado: Decimal | None
    rmi_projetada: Decimal | None
    rmi_valor_atual: Decimal | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Análise de Inconsistências ───────────────────────────────────────────────

class InconsistenciaItem(BaseModel):
    tipo: str
    descricao: str
    periodo_afetado: str | None = None
    impacto_financeiro: Decimal | None = None
    recomendacao: str | None = None


class AnaliseInconsistenciasResponse(BaseModel):
    cnis_id: uuid.UUID
    total_inconsistencias: int
    inconsistencias: list[InconsistenciaItem]
    periodos_sobrepostos: list[dict]
    salarios_suspeitos: list[dict]
    periodos_sem_remuneracao: list[dict]
