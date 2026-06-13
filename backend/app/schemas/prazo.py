import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


TipoPrazoType = Literal[
    "CONTESTACAO", "RECURSO", "CONTRARRAZOES", "MANIFESTACAO",
    "CUMPRIMENTO_SENTENCA", "OUTROS"
]


class PrazoCreate(BaseModel):
    tipo_prazo: TipoPrazoType = "OUTROS"
    descricao: str = Field(..., max_length=300)
    dias_corridos: int = Field(..., gt=0)
    data_inicio: date
    observacao: str | None = None
    movimentacao_id: uuid.UUID | None = None


class PrazoUpdate(BaseModel):
    concluido: bool | None = None
    observacao: str | None = None


class PrazoResponse(BaseModel):
    id: uuid.UUID
    processo_id: uuid.UUID
    movimentacao_id: uuid.UUID | None
    tipo_prazo: str
    descricao: str
    dias_corridos: int
    dias_uteis: int
    data_inicio: date
    data_vencimento: date
    concluido: bool
    observacao: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
