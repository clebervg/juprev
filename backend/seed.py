"""
Script para criar o tenant inicial e o usuário administrador.
Execute a partir da pasta backend/ com o env ativo:

    python seed.py
"""
import asyncio
import uuid

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.user import User


async def main() -> None:
    print("\n=== Juprev — Criação do Admin ===\n")

    tenant_name = input("Nome do escritório: ").strip()
    cnpj = input("CNPJ (formato 00.000.000/0000-00): ").strip()
    email = input("E-mail do admin: ").strip()
    full_name = input("Nome completo do admin: ").strip()
    password = input("Senha (mín. 8 chars, 1 maiúscula, 1 número): ").strip()

    async with AsyncSessionLocal() as db:
        # Verifica se o tenant já existe
        result = await db.execute(select(Tenant).where(Tenant.cnpj == cnpj))
        tenant = result.scalar_one_or_none()

        if tenant:
            print(f"\nTenant com CNPJ {cnpj} já existe. Usando o existente.")
        else:
            tenant = Tenant(
                id=uuid.uuid4(),
                name=tenant_name,
                cnpj=cnpj,
                is_active=True,
            )
            db.add(tenant)
            await db.flush()
            print(f"\nTenant criado: {tenant.name} (id={tenant.id})")

        # Verifica se o usuário já existe
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"Usuário {email} já existe. Nenhuma alteração feita.")
        else:
            admin = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name,
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)
            print(f"Usuário admin criado: {email}")

        await db.commit()

    print("\nPronto! Use as credenciais acima para fazer login.\n")


if __name__ == "__main__":
    asyncio.run(main())
