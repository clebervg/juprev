import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.processo import ProcessoJudicial
    from app.models.movimentacao import MovimentacaoProcessual


class PrazoProcessual(Base):
    __tablename__ = "prazos_processuais"

    processo_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("processos_judiciais.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    movimentacao_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("movimentacoes_processuais.id", ondelete="SET NULL"),
        nullable=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    tipo_prazo: Mapped[str] = mapped_column(
        Enum(
            "CONTESTACAO", "RECURSO", "CONTRARRAZOES", "MANIFESTACAO",
            "CUMPRIMENTO_SENTENCA", "OUTROS",
            name="tipo_prazo_enum",
        ),
        nullable=False, default="OUTROS",
    )
    descricao: Mapped[str] = mapped_column(String(300), nullable=False)
    dias_corridos: Mapped[int] = mapped_column(Integer, nullable=False)
    dias_uteis: Mapped[int] = mapped_column(Integer, nullable=False)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    concluido: Mapped[bool] = mapped_column(Boolean, default=False)
    observacao: Mapped[str | None] = mapped_column(Text)

    processo: Mapped["ProcessoJudicial"] = relationship(back_populates="prazos")
    movimentacao: Mapped["MovimentacaoProcessual | None"] = relationship(
        foreign_keys=[movimentacao_id]
    )
