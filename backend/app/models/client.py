import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (
        # CPF e NIS são únicos dentro do mesmo tenant (isolamento multi-tenant).
        UniqueConstraint("tenant_id", "cpf", name="uq_client_tenant_cpf"),
        UniqueConstraint("tenant_id", "nis", name="uq_client_tenant_nis"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # Dados pessoais
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    # LGPD: CPF é dado sensível — nunca logar, nunca expor em erros.
    cpf: Mapped[str | None] = mapped_column(String(11), nullable=True)
    rg: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rg_orgao_expedidor: Mapped[str | None] = mapped_column(String(10))
    data_nascimento: Mapped[Date | None] = mapped_column(Date, nullable=True)
    nome_mae: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nome_pai: Mapped[str | None] = mapped_column(String(255))
    estado_civil: Mapped[str | None] = mapped_column(
        Enum("solteiro", "casado", "divorciado", "viuvo", "uniao_estavel", name="estado_civil_enum"),
    )
    genero: Mapped[str | None] = mapped_column(
        Enum("masculino", "feminino", "outro", name="genero_enum"),
    )
    nis: Mapped[str | None] = mapped_column(String(11), nullable=True)
    ctps_numero: Mapped[str | None] = mapped_column(String(10))
    ctps_serie: Mapped[str | None] = mapped_column(String(5))
    escolaridade: Mapped[str | None] = mapped_column(String(50))
    profissao: Mapped[str | None] = mapped_column(String(100))

    # Contato
    email: Mapped[str | None] = mapped_column(String(255))
    telefone_celular: Mapped[str | None] = mapped_column(String(20))
    whatsapp: Mapped[bool] = mapped_column(Boolean, default=True)
    telefone_fixo: Mapped[str | None] = mapped_column(String(20))
    contato_emergencia_nome: Mapped[str | None] = mapped_column(String(255))
    contato_emergencia_telefone: Mapped[str | None] = mapped_column(String(20))

    # Endereço
    cep: Mapped[str | None] = mapped_column(String(8))
    logradouro: Mapped[str | None] = mapped_column(String(255))
    numero: Mapped[str | None] = mapped_column(String(10))
    complemento: Mapped[str | None] = mapped_column(String(50))
    bairro: Mapped[str | None] = mapped_column(String(100))
    cidade: Mapped[str | None] = mapped_column(String(100))
    uf: Mapped[str | None] = mapped_column(String(2))
    tipo_residencia: Mapped[str | None] = mapped_column(String(20))

    # Dados adicionais
    renda_mensal: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    possui_deficiencia: Mapped[bool] = mapped_column(Boolean, default=False)
    tipo_deficiencia: Mapped[str | None] = mapped_column(String(100))
    tempo_contribuicao_anos: Mapped[int | None] = mapped_column(Integer)
    observacoes: Mapped[str | None] = mapped_column(Text)

    dependentes: Mapped[list["Dependente"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )


class Dependente(Base):
    __tablename__ = "dependentes"

    cliente_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    cpf: Mapped[str | None] = mapped_column(String(11))
    data_nascimento: Mapped[Date | None] = mapped_column(Date)
    parentesco: Mapped[str | None] = mapped_column(
        Enum("filho", "conjuge", "companheiro", "outros", name="parentesco_enum"),
    )
    e_beneficiario: Mapped[bool] = mapped_column(Boolean, default=False)
    percentual_dependencia: Mapped[int | None] = mapped_column(Integer)

    cliente: Mapped["Client"] = relationship(back_populates="dependentes")
