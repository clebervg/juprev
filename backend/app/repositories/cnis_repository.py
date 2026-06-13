import uuid
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base import Base
from app.models.cnis import CNIS, CNISPeriodoContribuicao, CNISRemuneracao, CalculoRMI, SimulacaoCenario
from app.repositories.base import BaseRepository


class CNISRepository(BaseRepository[CNIS]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(CNIS, db)

    async def get_by_tenant(
        self,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[CNIS], int]:
        count_q = select(func.count()).select_from(CNIS).where(CNIS.tenant_id == tenant_id)
        total = (await self.db.execute(count_q)).scalar_one()

        q = (
            select(CNIS)
            .where(CNIS.tenant_id == tenant_id)
            .order_by(CNIS.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = (await self.db.execute(q)).scalars().all()
        return list(rows), total

    async def get_by_cliente(
        self, cliente_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[CNIS]:
        q = (
            select(CNIS)
            .where(CNIS.cliente_id == cliente_id, CNIS.tenant_id == tenant_id)
            .order_by(CNIS.created_at.desc())
        )
        return list((await self.db.execute(q)).scalars().all())

    async def get_by_id_and_tenant(
        self, cnis_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> CNIS | None:
        q = (
            select(CNIS)
            .where(CNIS.id == cnis_id, CNIS.tenant_id == tenant_id)
            .options(
                selectinload(CNIS.periodos_contribuicao).selectinload(
                    CNISPeriodoContribuicao.remuneracoes
                ),
                selectinload(CNIS.calculos_rmi),
            )
        )
        return (await self.db.execute(q)).scalar_one_or_none()

    async def hash_existe(self, arquivo_hash: str, tenant_id: uuid.UUID) -> bool:
        q = select(CNIS.id).where(
            CNIS.arquivo_original_hash == arquivo_hash,
            CNIS.tenant_id == tenant_id,
        )
        return (await self.db.execute(q)).scalar_one_or_none() is not None

    async def get_remuneracoes(
        self,
        cnis_id: uuid.UUID,
        tenant_id: uuid.UUID,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> list[CNISRemuneracao]:
        # Valida pertença ao tenant antes de acessar os dados
        cnis = await self.get_by_id_and_tenant(cnis_id, tenant_id)
        if not cnis:
            return []

        q = (
            select(CNISRemuneracao)
            .where(CNISRemuneracao.cnis_id == cnis_id)
            .order_by(CNISRemuneracao.mes_referencia)
        )
        if data_inicio:
            q = q.where(CNISRemuneracao.mes_referencia >= data_inicio)
        if data_fim:
            q = q.where(CNISRemuneracao.mes_referencia <= data_fim)

        return list((await self.db.execute(q)).scalars().all())


class CalculoRMIRepository(BaseRepository[CalculoRMI]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(CalculoRMI, db)

    async def get_by_cnis(
        self, cnis_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[CalculoRMI]:
        q = (
            select(CalculoRMI)
            .where(CalculoRMI.cnis_id == cnis_id, CalculoRMI.tenant_id == tenant_id)
            .order_by(CalculoRMI.created_at.desc())
        )
        return list((await self.db.execute(q)).scalars().all())

    async def get_by_id_and_tenant(
        self, calculo_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> CalculoRMI | None:
        q = select(CalculoRMI).where(
            CalculoRMI.id == calculo_id,
            CalculoRMI.tenant_id == tenant_id,
        )
        return (await self.db.execute(q)).scalar_one_or_none()


class SimulacaoRepository(BaseRepository[SimulacaoCenario]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(SimulacaoCenario, db)

    async def get_by_cnis(self, cnis_id: uuid.UUID) -> list[SimulacaoCenario]:
        q = (
            select(SimulacaoCenario)
            .where(SimulacaoCenario.cnis_id == cnis_id)
            .order_by(SimulacaoCenario.data_simulacao_futura)
        )
        return list((await self.db.execute(q)).scalars().all())
