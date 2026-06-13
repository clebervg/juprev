import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.alerta import AlertaProcessual
from app.models.user import User
from app.repositories.movimentacao_repository import MovimentacaoRepository
from app.schemas.alerta import AlertaListResponse, AlertaResponse

router = APIRouter(prefix="/alertas", tags=["alertas"])


@router.get("", response_model=AlertaListResponse)
async def listar_alertas(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    apenas_nao_lidos: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    repo = MovimentacaoRepository(db)
    items, total, nao_lidos = await repo.get_alertas_by_tenant(
        current_user.tenant_id, apenas_nao_lidos, skip, limit
    )
    return AlertaListResponse(items=items, total=total, nao_lidos=nao_lidos)


@router.patch("/{alerta_id}/lido", response_model=AlertaResponse)
async def marcar_lido(
    alerta_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(AlertaProcessual).where(
            AlertaProcessual.id == alerta_id,
            AlertaProcessual.tenant_id == current_user.tenant_id,
        )
    )
    alerta = result.scalar_one_or_none()
    if not alerta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta não encontrado.")

    alerta.lido = True
    await db.commit()
    await db.refresh(alerta)
    return alerta


@router.post("/marcar-todos-lidos", status_code=status.HTTP_204_NO_CONTENT)
async def marcar_todos_lidos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(AlertaProcessual).where(
            AlertaProcessual.tenant_id == current_user.tenant_id,
            AlertaProcessual.lido == False,
        )
    )
    for alerta in result.scalars().all():
        alerta.lido = True
    await db.commit()
