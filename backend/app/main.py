from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.models import Tenant, User, AuditLog, ProcessoJudicial, MovimentacaoProcessual, PrazoProcessual, AlertaProcessual  # noqa: F401 — registra mappers no SQLAlchemy
from app.core.config import settings
from app.core.logging import get_logger
from app.core.rate_limit import limiter
from app.jobs.rastreamento_job import iniciar_scheduler, parar_scheduler

logger = get_logger(__name__)

app = FastAPI(
    title="Juprev API",
    version="0.1.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

# Rate limiter — handler para 429
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Muitas tentativas. Aguarde alguns instantes e tente novamente."},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Juprev API iniciada. environment=%s", settings.ENVIRONMENT)
    iniciar_scheduler()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    parar_scheduler()
