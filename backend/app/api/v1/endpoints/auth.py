from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import limiter
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.session import get_db
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.services.auth_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Máximo 10 tentativas de login por minuto por IP."""
    return await authenticate_user(body.email, body.password, db)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh_token(
    request: Request,
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("tipo inválido")
        jti = payload.get("jti")
        if not jti:
            raise ValueError("jti ausente")
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido.",
        )

    repo = RefreshTokenRepository(db)
    if not await repo.is_valid(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revogado ou expirado.",
        )

    # Rotação: revoga o token atual e emite um novo par.
    await repo.revoke(jti)

    from uuid import UUID
    user_id = UUID(payload["sub"])
    tenant_id = UUID(payload["tenant_id"])

    new_refresh_str, new_jti, new_expires_at = create_refresh_token(user_id, tenant_id)
    await repo.create(jti=new_jti, user_id=user_id, expires_at=new_expires_at)

    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user_id, tenant_id),
        refresh_token=new_refresh_str,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, db: AsyncSession = Depends(get_db)) -> None:
    """Revoga o refresh token imediatamente."""
    try:
        payload = decode_token(body.refresh_token)
        jti = payload.get("jti")
    except JWTError:
        # Token inválido/expirado já é inútil; retorna 204 silenciosamente.
        return

    if jti:
        await RefreshTokenRepository(db).revoke(jti)
        await db.commit()
