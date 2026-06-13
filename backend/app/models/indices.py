from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IndiceCorrecao(Base):
    """
    Índices mensais de correção monetária (INPC, IPCA, IGP-D).

    indice_mensal: variação do mês em decimal (ex: 0.0054 = 0,54%)
    indice_acumulado: fator acumulado a partir de 01/07/1994 = 1.0
    Correção de um salário: salario * (acumulado_der / acumulado_competencia)
    """
    __tablename__ = "indices_correcao"
    __table_args__ = (
        UniqueConstraint("competencia", "fonte", name="uq_indice_competencia_fonte"),
    )

    competencia: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    fonte: Mapped[str] = mapped_column(
        Enum("INPC", "IPCA", "IGP-D", name="fonte_indice_enum"),
        nullable=False,
    )
    indice_mensal: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    indice_acumulado: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
