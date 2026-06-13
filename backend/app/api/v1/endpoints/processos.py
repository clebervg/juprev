import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.audit import registrar
from app.db.session import get_db
from app.models.user import User
from app.repositories.movimentacao_repository import MovimentacaoRepository
from app.repositories.processo_repository import ProcessoRepository
from app.schemas.movimentacao import MovimentacaoListResponse
from app.schemas.prazo import PrazoCreate, PrazoResponse, PrazoUpdate
from app.schemas.processo import ProcessoCreate, ProcessoListResponse, ProcessoResponse, ProcessoUpdate
from app.services.prazos_service import calcular_vencimento, calcular_dias_uteis_entre
from app.services.rastreamento_service import rastrear_processo
from app.models.processo import ProcessoJudicial
from app.models.prazo import PrazoProcessual

router = APIRouter(prefix="/processos", tags=["processos"])


@router.get("", response_model=ProcessoListResponse)
async def listar_processos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    apenas_ativos: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    repo = ProcessoRepository(db)
    items, total = await repo.get_by_tenant(current_user.tenant_id, skip, limit, apenas_ativos)
    return ProcessoListResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("", response_model=ProcessoResponse, status_code=status.HTTP_201_CREATED)
async def criar_processo(
    payload: ProcessoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    repo = ProcessoRepository(db)
    if await repo.numero_cnj_exists(payload.numero_cnj, current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Processo com este número CNJ já cadastrado para o seu escritório.",
        )

    processo = ProcessoJudicial(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        **payload.model_dump(),
    )
    db.add(processo)
    await db.flush()
    await registrar(
        db, tenant_id=current_user.tenant_id, user_id=current_user.id,
        entidade="processo", acao="criar", entidade_id=processo.id,
    )
    await db.commit()
    await db.refresh(processo)
    return processo


@router.get("/{processo_id}", response_model=ProcessoResponse)
async def obter_processo(
    processo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    repo = ProcessoRepository(db)
    processo = await repo.get_by_id_and_tenant(processo_id, current_user.tenant_id)
    if not processo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado.")
    return processo


@router.patch("/{processo_id}", response_model=ProcessoResponse)
async def atualizar_processo(
    processo_id: uuid.UUID,
    payload: ProcessoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    repo = ProcessoRepository(db)
    processo = await repo.get_by_id_and_tenant(processo_id, current_user.tenant_id)
    if not processo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado.")

    for campo, valor in payload.model_dump(exclude_none=True).items():
        setattr(processo, campo, valor)

    await registrar(
        db, tenant_id=current_user.tenant_id, user_id=current_user.id,
        entidade="processo", acao="editar", entidade_id=processo_id,
    )
    await db.commit()
    await db.refresh(processo)
    return processo


@router.delete("/{processo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_processo(
    processo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    repo = ProcessoRepository(db)
    processo = await repo.get_by_id_and_tenant(processo_id, current_user.tenant_id)
    if not processo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado.")

    await db.delete(processo)
    await registrar(
        db, tenant_id=current_user.tenant_id, user_id=current_user.id,
        entidade="processo", acao="excluir", entidade_id=processo_id,
    )
    await db.commit()


@router.get("/{processo_id}/movimentacoes", response_model=MovimentacaoListResponse)
async def listar_movimentacoes(
    processo_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    proc_repo = ProcessoRepository(db)
    processo = await proc_repo.get_by_id_and_tenant(processo_id, current_user.tenant_id)
    if not processo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado.")

    mov_repo = MovimentacaoRepository(db)
    items, total = await mov_repo.get_by_processo(processo_id, current_user.tenant_id, skip, limit)
    return MovimentacaoListResponse(items=items, total=total)


@router.post("/{processo_id}/sincronizar", response_model=dict)
async def sincronizar_processo(
    processo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Dispara consulta manual ao tribunal e persiste novas movimentações."""
    repo = ProcessoRepository(db)
    processo = await repo.get_by_id_and_tenant(processo_id, current_user.tenant_id)
    if not processo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado.")

    novas = await rastrear_processo(db, processo)
    await db.commit()
    return {"novas_movimentacoes": novas}


@router.get("/{processo_id}/prazos", response_model=list[PrazoResponse])
async def listar_prazos(
    processo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    proc_repo = ProcessoRepository(db)
    processo = await proc_repo.get_by_id_and_tenant(processo_id, current_user.tenant_id)
    if not processo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado.")

    mov_repo = MovimentacaoRepository(db)
    prazos = await mov_repo.get_prazos_by_processo(processo_id, current_user.tenant_id)
    return prazos


@router.post("/{processo_id}/prazos", response_model=PrazoResponse, status_code=status.HTTP_201_CREATED)
async def criar_prazo_manual(
    processo_id: uuid.UUID,
    payload: PrazoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    proc_repo = ProcessoRepository(db)
    processo = await proc_repo.get_by_id_and_tenant(processo_id, current_user.tenant_id)
    if not processo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado.")

    data_vencimento = calcular_vencimento(payload.data_inicio, payload.dias_corridos)
    dias_uteis = calcular_dias_uteis_entre(payload.data_inicio, data_vencimento)
    dias_corridos = (data_vencimento - payload.data_inicio).days

    prazo = PrazoProcessual(
        id=uuid.uuid4(),
        processo_id=processo_id,
        tenant_id=current_user.tenant_id,
        tipo_prazo=payload.tipo_prazo,
        descricao=payload.descricao,
        dias_corridos=dias_corridos,
        dias_uteis=dias_uteis,
        data_inicio=payload.data_inicio,
        data_vencimento=data_vencimento,
        observacao=payload.observacao,
        movimentacao_id=payload.movimentacao_id,
    )
    db.add(prazo)
    await db.flush()
    await registrar(
        db, tenant_id=current_user.tenant_id, user_id=current_user.id,
        entidade="prazo", acao="criar", entidade_id=prazo.id,
    )
    await db.commit()
    await db.refresh(prazo)
    return prazo


@router.patch("/{processo_id}/prazos/{prazo_id}", response_model=PrazoResponse)
async def atualizar_prazo(
    processo_id: uuid.UUID,
    prazo_id: uuid.UUID,
    payload: PrazoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    from sqlalchemy import select
    result = await db.execute(
        select(PrazoProcessual).where(
            PrazoProcessual.id == prazo_id,
            PrazoProcessual.processo_id == processo_id,
            PrazoProcessual.tenant_id == current_user.tenant_id,
        )
    )
    prazo = result.scalar_one_or_none()
    if not prazo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prazo não encontrado.")

    for campo, valor in payload.model_dump(exclude_none=True).items():
        setattr(prazo, campo, valor)

    await db.commit()
    await db.refresh(prazo)
    return prazo
