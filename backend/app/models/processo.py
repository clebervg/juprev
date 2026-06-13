import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.movimentacao import MovimentacaoProcessual
    from app.models.prazo import PrazoProcessual
    from app.models.alerta import AlertaProcessual


class ProcessoJudicial(Base):
    __tablename__ = "processos_judiciais"
    __table_args__ = (
        UniqueConstraint("tenant_id", "numero_cnj", name="uq_processo_tenant_cnj"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    numero_cnj: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    tribunal: Mapped[str] = mapped_column(
        Enum("TRF1", "TRF3", "TRF4", "TNU", "STJ", name="tribunal_enum"),
        nullable=False,
    )
    vara: Mapped[str | None] = mapped_column(String(200))
    comarca: Mapped[str | None] = mapped_column(String(100))
    uf: Mapped[str | None] = mapped_column(String(2))
    classe_processual: Mapped[str | None] = mapped_column(String(150))
    assunto: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Enum("ativo", "suspenso", "arquivado", "encerrado", name="status_processo_enum"),
        nullable=False, default="ativo",
    )
    monitoramento_ativo: Mapped[bool] = mapped_column(default=True)
    observacoes: Mapped[str | None] = mapped_column(Text)

    cliente: Mapped["Client | None"] = relationship(foreign_keys=[cliente_id])
    movimentacoes: Mapped[list["MovimentacaoProcessual"]] = relationship(
        back_populates="processo", cascade="all, delete-orphan",
        order_by="MovimentacaoProcessual.data_movimentacao.desc()",
    )
    prazos: Mapped[list["PrazoProcessual"]] = relationship(
        back_populates="processo", cascade="all, delete-orphan",
    )
    alertas: Mapped[list["AlertaProcessual"]] = relationship(
        back_populates="processo", cascade="all, delete-orphan",
    )
