import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.processo import ProcessoJudicial
    from app.models.movimentacao import MovimentacaoProcessual


class AlertaProcessual(Base):
    __tablename__ = "alertas_processuais"

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

    tipo: Mapped[str] = mapped_column(
        Enum(
            "NOVA_MOVIMENTACAO", "PRAZO_VENCENDO", "PRAZO_VENCIDO",
            "SENTENCA", "INTIMACAO",
            name="tipo_alerta_enum",
        ),
        nullable=False,
    )
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    lido: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    processo: Mapped["ProcessoJudicial"] = relationship(back_populates="alertas")
    movimentacao: Mapped["MovimentacaoProcessual | None"] = relationship(
        foreign_keys=[movimentacao_id]
    )
