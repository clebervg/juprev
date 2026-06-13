import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movimentacao import MovimentacaoProcessual
from app.models.prazo import PrazoProcessual
from app.models.alerta import AlertaProcessual
from app.repositories.base import BaseRepository


class MovimentacaoRepository(BaseRepository[MovimentacaoProcessual]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(MovimentacaoProcessual, db)

    async def get_by_processo(
        self,
        processo_id: uuid.UUID,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[MovimentacaoProcessual], int]:
        query = select(MovimentacaoProcessual).where(
            MovimentacaoProcessual.processo_id == processo_id,
            MovimentacaoProcessual.tenant_id == tenant_id,
        )
        total = (await self.db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
        result = await self.db.execute(
            query.order_by(MovimentacaoProcessual.data_movimentacao.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def hash_exists(self, processo_id: uuid.UUID, hash_conteudo: str) -> bool:
        result = await self.db.execute(
            select(MovimentacaoProcessual.id).where(
                MovimentacaoProcessual.processo_id == processo_id,
                MovimentacaoProcessual.hash_conteudo == hash_conteudo,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_prazos_by_processo(
        self, processo_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[PrazoProcessual]:
        result = await self.db.execute(
            select(PrazoProcessual).where(
                PrazoProcessual.processo_id == processo_id,
                PrazoProcessual.tenant_id == tenant_id,
            ).order_by(PrazoProcessual.data_vencimento)
        )
        return list(result.scalars().all())

    async def get_alertas_by_tenant(
        self,
        tenant_id: uuid.UUID,
        apenas_nao_lidos: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[AlertaProcessual], int, int]:
        """Retorna (alertas, total, nao_lidos)."""
        query = select(AlertaProcessual).where(AlertaProcessual.tenant_id == tenant_id)
        if apenas_nao_lidos:
            query = query.where(AlertaProcessual.lido == False)

        total = (await self.db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
        nao_lidos_result = await self.db.execute(
            select(func.count(AlertaProcessual.id)).where(
                AlertaProcessual.tenant_id == tenant_id,
                AlertaProcessual.lido == False,
            )
        )
        nao_lidos = nao_lidos_result.scalar_one()

        result = await self.db.execute(
            query.order_by(AlertaProcessual.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total, nao_lidos
