import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import registrar
from app.repositories.client_repository import ClientRepository
from app.schemas.client import ClientCreate, ClientUpdate


def _mask_cpf(cpf: str | None) -> str:
    if not cpf:
        return "Não informado"
    d = cpf.replace(".", "").replace("-", "")
    return f"***.***.*{d[-4:-2]}-{d[-2:]}" if len(d) == 11 else cpf


async def list_clients(
    tenant_id: uuid.UUID,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
) -> dict:
    repo = ClientRepository(db)
    clients, total = await repo.get_by_tenant(tenant_id, skip, limit, search)
    items = [
        {
            "id": str(c.id),
            "nome": c.nome,
            "cpf_mascarado": _mask_cpf(c.cpf),
            "telefone_celular": c.telefone_celular,
            "cidade": c.cidade,
            "uf": c.uf,
            "created_at": c.created_at,
        }
        for c in clients
    ]
    return {"items": items, "total": total, "skip": skip, "limit": limit}


async def get_client(client_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession):
    repo = ClientRepository(db)
    client = await repo.get_by_id_and_tenant(client_id, tenant_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")
    return client


async def create_client(
    data: ClientCreate,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
):
    repo = ClientRepository(db)

    if data.cpf and await repo.cpf_exists(data.cpf, tenant_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF já cadastrado neste escritório.")
    if data.nis and await repo.nis_exists(data.nis, tenant_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="NIS já cadastrado neste escritório.")

    dependentes_data = [d.model_dump() for d in data.dependentes]
    client_data = data.model_dump(exclude={"dependentes"})
    client = await repo.create_with_dependentes(tenant_id, client_data, dependentes_data)

    await registrar(db, tenant_id=tenant_id, user_id=user_id,
                    entidade="client", acao="criar", entidade_id=client.id,
                    detalhes=f"Cliente criado: {client.nome}")
    await db.commit()
    return await repo.get_by_id_and_tenant(client.id, tenant_id)


async def update_client(
    client_id: uuid.UUID,
    data: ClientUpdate,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
):
    repo = ClientRepository(db)
    client = await repo.get_by_id_and_tenant(client_id, tenant_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")

    updates = data.model_dump(exclude_none=True, exclude={"dependentes"})

    if "cpf" in updates and updates["cpf"] and await repo.cpf_exists(updates["cpf"], tenant_id, exclude_id=client_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF já cadastrado neste escritório.")
    if "nis" in updates and updates["nis"] and await repo.nis_exists(updates["nis"], tenant_id, exclude_id=client_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="NIS já cadastrado neste escritório.")

    for field, value in updates.items():
        setattr(client, field, value)

    if data.dependentes is not None:
        dependentes_data = [d.model_dump() for d in data.dependentes]
        await repo.replace_dependentes(client_id, tenant_id, dependentes_data)

    campos = ", ".join(updates.keys()) or "dependentes"
    await registrar(db, tenant_id=tenant_id, user_id=user_id,
                    entidade="client", acao="editar", entidade_id=client_id,
                    detalhes=f"Campos alterados: {campos}")
    await db.commit()
    return await repo.get_by_id_and_tenant(client_id, tenant_id)


async def delete_client(
    client_id: uuid.UUID,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    repo = ClientRepository(db)
    client = await repo.get_by_id_and_tenant(client_id, tenant_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")

    await registrar(db, tenant_id=tenant_id, user_id=user_id,
                    entidade="client", acao="excluir", entidade_id=client_id,
                    detalhes=f"Cliente excluído: {client.nome}")
    await db.delete(client)
    await db.commit()
