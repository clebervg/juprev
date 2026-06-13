import uuid
from typing import Any

from sqlalchemy import Enum, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False), nullable=False, index=True
    )
    entidade: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entidade_id: Mapped[str | None] = mapped_column(String(36))
    acao: Mapped[str] = mapped_column(
        Enum("criar", "editar", "excluir", "visualizar", "exportar", name="audit_acao_enum"),
        nullable=False,
    )
    detalhes: Mapped[str | None] = mapped_column(Text)
