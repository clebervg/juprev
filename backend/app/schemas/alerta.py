import uuid
from datetime import datetime

from pydantic import BaseModel


class AlertaResponse(BaseModel):
    id: uuid.UUID
    processo_id: uuid.UUID
    movimentacao_id: uuid.UUID | None
    tipo: str
    mensagem: str
    lido: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertaListResponse(BaseModel):
    items: list[AlertaResponse]
    total: int
    nao_lidos: int
