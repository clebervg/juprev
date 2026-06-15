from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import Date, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SalarioMinimo(Base):
    """
    Histórico de salários mínimos brasileiros por período de vigência.

    Para consultar o salário mínimo vigente em uma data D:
        SELECT valor FROM salario_minimo
        WHERE vigencia_inicio <= D
        ORDER BY vigencia_inicio DESC LIMIT 1
    """

    __tablename__ = "salario_minimo"
    __table_args__ = (Index("ix_salario_minimo_vigencia", "vigencia_inicio"),)

    vigencia_inicio: Mapped[datetime.date] = mapped_column(Date, nullable=False, unique=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
