from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.services import indices_service

router = APIRouter(prefix="/indices", tags=["indices"])


@router.get("")
async def listar_indices(
    fonte: str = Query("INPC", pattern="^(INPC|IPCA|IGP-D)$"),
    ano: int | None = Query(None, ge=1994, le=2100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[dict]:
    rows = await indices_service.listar_indices(db, fonte, ano)
    return [
        {
            "competencia": str(r.competencia),
            "fonte": r.fonte,
            "indice_mensal_pct": float(r.indice_mensal * 100),
            "indice_acumulado": float(r.indice_acumulado),
        }
        for r in rows
    ]


@router.get("/fator")
async def fator_correcao(
    competencia: date = Query(..., description="Competência do salário (YYYY-MM-DD)"),
    data_der: date = Query(..., description="Data de Entrada do Requerimento"),
    fonte: str = Query("INPC", pattern="^(INPC|IPCA|IGP-D)$"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> dict:
    """Retorna o fator de correção de uma competência até a DER."""
    fatores = await indices_service.carregar_fatores_correcao(db, data_der, fonte)
    comp_normalizada = date(competencia.year, competencia.month, 1)
    fator = fatores.get(comp_normalizada)
    return {
        "competencia": str(comp_normalizada),
        "data_der": str(data_der),
        "fonte": fonte,
        "fator": float(fator) if fator else None,
        "disponivel": fator is not None,
    }
