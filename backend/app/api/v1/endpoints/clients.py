import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.audit import registrar
from app.db.session import get_db
from app.models.user import User
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.services import client_service

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=dict)
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await client_service.list_clients(current_user.tenant_id, db, skip, limit, search)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    client = await client_service.get_client(client_id, current_user.tenant_id, db)
    await registrar(db, tenant_id=current_user.tenant_id, user_id=current_user.id,
                    entidade="client", acao="visualizar", entidade_id=client_id)
    await db.commit()
    return client


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    body: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await client_service.create_client(body, current_user.tenant_id, current_user.id, db)


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: uuid.UUID,
    body: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await client_service.update_client(client_id, body, current_user.tenant_id, current_user.id, db)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await client_service.delete_client(client_id, current_user.tenant_id, current_user.id, db)


@router.get("/{client_id}/export")
async def export_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Exporta todos os dados do cliente em JSON — direito de portabilidade LGPD."""
    client = await client_service.get_client(client_id, current_user.tenant_id, db)

    await registrar(db, tenant_id=current_user.tenant_id, user_id=current_user.id,
                    entidade="client", acao="exportar", entidade_id=client_id)
    await db.commit()

    export = {
        "exportado_por": str(current_user.id),
        "dados_pessoais": {
            "nome": client.nome,
            "cpf": client.cpf,
            "rg": client.rg,
            "data_nascimento": str(client.data_nascimento) if client.data_nascimento else None,
            "nome_mae": client.nome_mae,
            "nome_pai": client.nome_pai,
            "estado_civil": client.estado_civil,
            "genero": client.genero,
            "nis": client.nis,
            "escolaridade": client.escolaridade,
            "profissao": client.profissao,
        },
        "contato": {
            "email": client.email,
            "telefone_celular": client.telefone_celular,
            "telefone_fixo": client.telefone_fixo,
            "contato_emergencia_nome": client.contato_emergencia_nome,
            "contato_emergencia_telefone": client.contato_emergencia_telefone,
        },
        "endereco": {
            "cep": client.cep,
            "logradouro": client.logradouro,
            "numero": client.numero,
            "complemento": client.complemento,
            "bairro": client.bairro,
            "cidade": client.cidade,
            "uf": client.uf,
            "tipo_residencia": client.tipo_residencia,
        },
        "financeiro": {
            "renda_mensal": float(client.renda_mensal) if client.renda_mensal else None,
        },
        "dependentes": [
            {
                "nome": d.nome,
                "cpf": d.cpf,
                "data_nascimento": str(d.data_nascimento) if d.data_nascimento else None,
                "parentesco": d.parentesco,
                "e_beneficiario": d.e_beneficiario,
                "percentual_dependencia": d.percentual_dependencia,
            }
            for d in client.dependentes
        ],
        "cadastro": {
            "criado_em": client.created_at.isoformat(),
        },
    }

    return JSONResponse(
        content=export,
        headers={"Content-Disposition": f'attachment; filename="cliente_{client_id}.json"'},
    )
