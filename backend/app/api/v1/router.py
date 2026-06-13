from fastapi import APIRouter

from app.api.v1.endpoints import auth, clients, cnis, health, indices, users, processos, alertas

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(clients.router)
api_router.include_router(cnis.router)
api_router.include_router(indices.router)
api_router.include_router(processos.router)
api_router.include_router(alertas.router)
