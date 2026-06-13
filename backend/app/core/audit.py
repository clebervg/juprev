import uuid
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

AuditAcao = Literal["criar", "editar", "excluir", "visualizar", "exportar"]


async def registrar(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    entidade: str,
    acao: AuditAcao,
    entidade_id: uuid.UUID | str | None = None,
    detalhes: str | None = None,
) -> None:
    """Grava um registro de auditoria. Deve ser chamado antes do commit da operação principal."""
    log = AuditLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        entidade=entidade,
        entidade_id=str(entidade_id) if entidade_id else None,
        acao=acao,
        detalhes=detalhes,
    )
    db.add(log)
