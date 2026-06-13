import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.processo import ProcessoJudicial


class MovimentacaoProcessual(Base):
    __tablename__ = "movimentacoes_processuais"
    __table_args__ = (
        # hash_conteudo garante idempotência: não duplica a mesma movimentação.
        UniqueConstraint("processo_id", "hash_conteudo", name="uq_movimentacao_hash"),
    )

    processo_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("processos_judiciais.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    data_movimentacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(
        Enum(
            "INTIMACAO", "SENTENCA", "DESPACHO", "ACORDAO",
            "RECURSO", "PETICAO", "OUTROS",
            name="tipo_movimentacao_enum",
        ),
        nullable=False, default="OUTROS",
    )
    hash_conteudo: Mapped[str] = mapped_column(String(64), nullable=False)
    origem_tribunal: Mapped[str | None] = mapped_column(String(10))
    documento_url: Mapped[str | None] = mapped_column(Text)

    processo: Mapped["ProcessoJudicial"] = relationship(back_populates="movimentacoes")
