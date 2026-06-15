import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CNIS(Base):
    __tablename__ = "cnis"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # LGPD: nome e CPF são dados sensíveis — nunca logar.
    nome_segurado: Mapped[str] = mapped_column(String(255), nullable=False)
    cpf: Mapped[str] = mapped_column(String(11), nullable=False)
    nis: Mapped[str | None] = mapped_column(String(11), nullable=True)
    data_nascimento: Mapped[Date] = mapped_column(Date, nullable=False)

    arquivo_original_nome: Mapped[str | None] = mapped_column(String(255))
    arquivo_original_hash: Mapped[str | None] = mapped_column(String(64))  # SHA-256 evita duplicação
    periodo_inicial_cn: Mapped[Date | None] = mapped_column(Date)
    periodo_final_cn: Mapped[Date | None] = mapped_column(Date)

    # Totalizadores calculados no processamento
    tempo_contribuicao_total_dias: Mapped[int | None] = mapped_column(Integer)
    tempo_contribuicao_anos: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    total_contribuicoes: Mapped[int | None] = mapped_column(Integer)
    maior_salario_contribuicao: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    media_salarios_contribuicao: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    media_salarios_contribuicao_corrigida: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    status_processamento: Mapped[str] = mapped_column(
        Enum("pendente", "processando", "concluido", "erro", name="cnis_status_enum"),
        default="pendente", nullable=False,
    )
    erros_validacao: Mapped[dict | None] = mapped_column(JSON)

    periodos_contribuicao: Mapped[list["CNISPeriodoContribuicao"]] = relationship(
        back_populates="cnis", cascade="all, delete-orphan",
    )
    remuneracoes: Mapped[list["CNISRemuneracao"]] = relationship(
        back_populates="cnis", cascade="all, delete-orphan",
    )
    calculos_rmi: Mapped[list["CalculoRMI"]] = relationship(
        back_populates="cnis", cascade="all, delete-orphan",
    )
    simulacoes: Mapped[list["SimulacaoCenario"]] = relationship(
        back_populates="cnis", cascade="all, delete-orphan",
    )


class CNISPeriodoContribuicao(Base):
    __tablename__ = "cnis_periodos_contribuicao"

    cnis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("cnis.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    cnpj_empregador: Mapped[str | None] = mapped_column(String(14))
    razao_social_empregador: Mapped[str | None] = mapped_column(String(255))

    data_inicio: Mapped[Date] = mapped_column(Date, nullable=False)
    data_fim: Mapped[Date | None] = mapped_column(Date)

    tipo_contribuinte: Mapped[str | None] = mapped_column(
        Enum(
            "empregado", "empregador", "contribuinte_individual",
            "segurado_especial", "facultativo", "estagiario",
            "avulso", "dirigente_sindical",
            name="tipo_contribuinte_enum",
        )
    )
    categoria: Mapped[str | None] = mapped_column(String(10))

    dias_contribuidos: Mapped[int] = mapped_column(Integer, nullable=False)

    # Indicadores de modalidades especiais
    indicador_aposentadoria_especial: Mapped[bool] = mapped_column(Boolean, default=False)
    agente_nocivo: Mapped[str | None] = mapped_column(String(100))
    grau_deficiencia: Mapped[str | None] = mapped_column(
        Enum("leve", "moderada", "grave", name="grau_deficiencia_enum")
    )

    total_remuneracoes: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    quantidade_remuneracoes: Mapped[int | None] = mapped_column(Integer)

    observacoes: Mapped[str | None] = mapped_column(Text)
    periodo_valido: Mapped[bool] = mapped_column(Boolean, default=True)
    motivo_invalidacao: Mapped[str | None] = mapped_column(String(255))

    cnis: Mapped["CNIS"] = relationship(back_populates="periodos_contribuicao")
    remuneracoes: Mapped[list["CNISRemuneracao"]] = relationship(
        back_populates="periodo", cascade="all, delete-orphan",
    )


class CNISRemuneracao(Base):
    __tablename__ = "cnis_remuneracoes"

    cnis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("cnis.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    periodo_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("cnis_periodos_contribuicao.id", ondelete="SET NULL"),
    )

    # Primeiro dia do mês (YYYY-MM-01)
    mes_referencia: Mapped[Date] = mapped_column(Date, nullable=False)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)

    salario_contribuicao: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    salario_contribuicao_corrigido: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    teto_inss: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    base_calculo: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    tipo_remuneracao: Mapped[str | None] = mapped_column(
        Enum(
            "salario", "13o_salario", "ferias", "rescisao",
            "adicional_noturno", "hora_extra", "comissao",
            "gratificacao", "outros",
            name="tipo_remuneracao_enum",
        )
    )

    contribuiu_inss: Mapped[bool] = mapped_column(Boolean, default=True)
    valor_contribuicao: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    salario_valido: Mapped[bool] = mapped_column(Boolean, default=True)
    acima_teto: Mapped[bool] = mapped_column(Boolean, default=False)
    abaixo_minimo: Mapped[bool] = mapped_column(Boolean, default=False)

    cnis: Mapped["CNIS"] = relationship(back_populates="remuneracoes")
    periodo: Mapped["CNISPeriodoContribuicao | None"] = relationship(back_populates="remuneracoes")


class CalculoRMI(Base):
    __tablename__ = "calculos_rmi"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    cnis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("cnis.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    calculado_por: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("users.id", ondelete="SET NULL"),
    )

    nome_calculo: Mapped[str] = mapped_column(String(100), nullable=False)

    tipo_beneficio: Mapped[str] = mapped_column(
        Enum(
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
            name="tipo_beneficio_enum",
        ),
        nullable=False,
    )

    regra_aplicada: Mapped[str | None] = mapped_column(String(100))

    # DER = Data de Entrada do Requerimento (real ou simulada)
    data_der: Mapped[Date] = mapped_column(Date, nullable=False)
    idade_na_der: Mapped[int] = mapped_column(Integer, nullable=False)
    tempo_contribuicao_na_der: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    salario_beneficio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    coeficiente_calculo: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    fator_previdenciario: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    fator_acumulador: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))

    rmi_calculada: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    rmi_teto: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    rmi_final: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # JSON com passo-a-passo auditável do cálculo
    detalhamento_calculo: Mapped[dict] = mapped_column(JSON, nullable=False)
    requisitos_atendidos: Mapped[dict | None] = mapped_column(JSON)

    rmi_regra_anterior: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    diferenca_reforma: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    calculo_valido: Mapped[bool] = mapped_column(Boolean, default=True)
    alertas: Mapped[list | None] = mapped_column(JSON)
    erros: Mapped[list | None] = mapped_column(JSON)

    versao_calculo: Mapped[str | None] = mapped_column(String(20))

    cnis: Mapped["CNIS"] = relationship(back_populates="calculos_rmi")


class SimulacaoCenario(Base):
    __tablename__ = "simulacoes_cenarios"

    cnis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("cnis.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    nome_simulacao: Mapped[str | None] = mapped_column(String(100))
    data_simulacao_futura: Mapped[Date] = mapped_column(Date, nullable=False)

    taxa_crescimento_salario: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    taxa_inflacao_anual: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))

    idade_na_data: Mapped[int | None] = mapped_column(Integer)
    tempo_contribuicao_projetado: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    salario_beneficio_projetado: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    rmi_projetada: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    rmi_valor_atual: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    cnis: Mapped["CNIS"] = relationship(back_populates="simulacoes")
