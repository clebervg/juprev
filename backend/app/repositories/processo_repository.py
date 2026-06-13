import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.processo import ProcessoJudicial
from app.repositories.base import BaseRepository


class ProcessoRepository(BaseRepository[ProcessoJudicial]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ProcessoJudicial, db)

    async def get_by_tenant(
        self,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        apenas_ativos: bool = False,
    ) -> tuple[list[ProcessoJudicial], int]:
        """Retorna lista paginada filtrada por tenant."""
        query = select(ProcessoJudicial).where(ProcessoJudicial.tenant_id == tenant_id)
        if apenas_ativos:
            query = query.where(ProcessoJudicial.status == "ativo")

        total = (await self.db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
        result = await self.db.execute(
            query.order_by(ProcessoJudicial.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_id_and_tenant(
        self, id: uuid.UUID, tenant_id: uuid.UUID
    ) -> ProcessoJudicial | None:
        result = await self.db.execute(
            select(ProcessoJudicial)
            .where(ProcessoJudicial.id == id, ProcessoJudicial.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_monitorados(self) -> list[ProcessoJudicial]:
        """Retorna todos os processos com monitoramento ativo (todos os tenants) — usado pelo job."""
        result = await self.db.execute(
            select(ProcessoJudicial)
            .where(
                ProcessoJudicial.monitoramento_ativo == True,
                ProcessoJudicial.status == "ativo",
            )
        )
        return list(result.scalars().all())

    async def numero_cnj_exists(
        self, numero_cnj: str, tenant_id: uuid.UUID, exclude_id: uuid.UUID | None = None
    ) -> bool:
        query = select(ProcessoJudicial.id).where(
            ProcessoJudicial.numero_cnj == numero_cnj,
            ProcessoJudicial.tenant_id == tenant_id,
        )
        if exclude_id:
            query = query.where(ProcessoJudicial.id != exclude_id)
        return (await self.db.execute(query)).scalar_one_or_none() is not None
