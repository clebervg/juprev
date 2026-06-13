import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


TipoMovimentacaoType = Literal[
    "INTIMACAO", "SENTENCA", "DESPACHO", "ACORDAO", "RECURSO", "PETICAO", "OUTROS"
]


class MovimentacaoResponse(BaseModel):
    id: uuid.UUID
    processo_id: uuid.UUID
    data_movimentacao: datetime
    descricao: str
    tipo: str
    origem_tribunal: str | None
    documento_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MovimentacaoListResponse(BaseModel):
    items: list[MovimentacaoResponse]
    total: int
