import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.client import Client, Dependente
from app.repositories.base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Client, db)

    async def get_by_tenant(
        self,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> tuple[list[Client], int]:
        """Retorna lista paginada e total — SEMPRE filtrado por tenant_id."""
        query = select(Client).where(Client.tenant_id == tenant_id)
        if search:
            query = query.where(Client.nome.ilike(f"%{search}%"))

        total_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar_one()

        result = await self.db.execute(
            query.order_by(Client.nome).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_id_and_tenant(
        self, id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Client | None:
        """Busca por ID garantindo que pertence ao tenant. Carrega dependentes."""
        result = await self.db.execute(
            select(Client)
            .where(Client.id == id, Client.tenant_id == tenant_id)
            .options(selectinload(Client.dependentes))
        )
        return result.scalar_one_or_none()

    async def cpf_exists(self, cpf: str, tenant_id: uuid.UUID, exclude_id: uuid.UUID | None = None) -> bool:
        query = select(Client.id).where(Client.cpf == cpf, Client.tenant_id == tenant_id)
        if exclude_id:
            query = query.where(Client.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def nis_exists(self, nis: str, tenant_id: uuid.UUID, exclude_id: uuid.UUID | None = None) -> bool:
        query = select(Client.id).where(Client.nis == nis, Client.tenant_id == tenant_id)
        if exclude_id:
            query = query.where(Client.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def replace_dependentes(
        self,
        client_id: uuid.UUID,
        tenant_id: uuid.UUID,
        dependentes_data: list[dict],
    ) -> None:
        """Remove todos os dependentes existentes e recria com os novos dados."""
        existing = await self.db.execute(
            select(Dependente).where(Dependente.cliente_id == client_id)
        )
        for dep in existing.scalars().all():
            await self.db.delete(dep)

        for dep in dependentes_data:
            self.db.add(Dependente(
                id=uuid.uuid4(),
                cliente_id=client_id,
                tenant_id=tenant_id,
                **dep,
            ))

    async def create_with_dependentes(
        self,
        tenant_id: uuid.UUID,
        data: dict,
        dependentes_data: list[dict],
    ) -> Client:
        dependentes_raw = dependentes_data
        client = Client(id=uuid.uuid4(), tenant_id=tenant_id, **data)
        self.db.add(client)
        await self.db.flush()

        for dep in dependentes_raw:
            dependente = Dependente(
                id=uuid.uuid4(),
                cliente_id=client.id,
                tenant_id=tenant_id,
                **dep,
            )
            self.db.add(dependente)

        await self.db.flush()

        # Recarrega com dependentes para não disparar lazy load fora da sessão.
        result = await self.db.execute(
            select(Client)
            .where(Client.id == client.id)
            .options(selectinload(Client.dependentes))
        )
        return result.scalar_one()
