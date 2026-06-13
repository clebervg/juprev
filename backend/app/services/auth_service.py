from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse

logger = get_logger(__name__)

# LGPD: mensagem de erro genérica — não revela se o email existe ou não.
_INVALID_CREDENTIALS = "Credenciais inválidas."


async def authenticate_user(
    email: str, password: str, db: AsyncSession
) -> TokenResponse:
    from fastapi import HTTPException, status

    repo = UserRepository(db)
    user = await repo.get_by_email(email)

    # Verifica hash mesmo quando user não existe para evitar timing attack.
    dummy_hash = "$2b$12$KIXtPbzjlwVuFtxlmRfxuOeB5P5n5E3v3q1yKq6h7y8j9z0a1b2c3"
    password_ok = verify_password(password, user.hashed_password if user else dummy_hash)

    if not user or not password_ok or not user.is_active:
        # LGPD: log sem email para não vazar dado pessoal.
        logger.warning("Tentativa de login com credenciais inválidas.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("Login bem-sucedido. user_id=%s tenant_id=%s", user.id, user.tenant_id)
    return TokenResponse(
        access_token=create_access_token(user.id, user.tenant_id),
        refresh_token=create_refresh_token(user.id, user.tenant_id),
    )
