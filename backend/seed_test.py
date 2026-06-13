"""
Cria escritório e admin de teste para desenvolvimento local.
Execute a partir da pasta backend/ com o env ativo:

    python seed_test.py
"""
import asyncio
import uuid

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.user import User

TENANT = {
    "name": "Escritório Cleber",
    "cnpj": "70.000.000/0001-00",
}

ADMIN = {
    "email": "clebervg@gmail.com",
    "full_name": "Cleber Gonçalves",
    "password": "cleber01",
}


async def main() -> None:
    async with AsyncSessionLocal() as db:
        tenant = Tenant(
            id=uuid.uuid4(),
            name=TENANT["name"],
            cnpj=TENANT["cnpj"],
            is_active=True,
        )
        db.add(tenant)
        await db.flush()

        admin = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email=ADMIN["email"],
            hashed_password=hash_password(ADMIN["password"]),
            full_name=ADMIN["full_name"],
            is_active=True,
            is_superuser=True,
        )
        db.add(admin)
        await db.commit()

    print("\n✓ Dados de teste criados:")
    print(f"  Escritório : {TENANT['name']}")
    print(f"  E-mail     : {ADMIN['email']}")
    print(f"  Senha      : {ADMIN['password']}\n")


if __name__ == "__main__":
    asyncio.run(main())
