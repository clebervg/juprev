import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


TribunalType = Literal["TRF1", "TRF3", "TRF4", "TNU", "STJ"]
StatusProcessoType = Literal["ativo", "suspenso", "arquivado", "encerrado"]

_CNJ_RE = re.compile(r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$")


class ProcessoCreate(BaseModel):
    numero_cnj: str = Field(..., description="Número no formato CNJ: 0000000-00.0000.0.00.0000")
    tribunal: TribunalType
    cliente_id: uuid.UUID | None = None
    vara: str | None = None
    comarca: str | None = None
    uf: str | None = Field(None, max_length=2)
    classe_processual: str | None = None
    assunto: str | None = None
    observacoes: str | None = None

    @field_validator("numero_cnj")
    @classmethod
    def valida_cnj(cls, v: str) -> str:
        normalizado = v.strip().replace(" ", "")
        if not _CNJ_RE.match(normalizado):
            raise ValueError("Número CNJ inválido. Use o formato: 0000000-00.0000.0.00.0000")
        return normalizado


class ProcessoUpdate(BaseModel):
    vara: str | None = None
    comarca: str | None = None
    uf: str | None = Field(None, max_length=2)
    classe_processual: str | None = None
    assunto: str | None = None
    status: StatusProcessoType | None = None
    monitoramento_ativo: bool | None = None
    observacoes: str | None = None


class ProcessoResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    cliente_id: uuid.UUID | None
    numero_cnj: str
    tribunal: str
    vara: str | None
    comarca: str | None
    uf: str | None
    classe_processual: str | None
    assunto: str | None
    status: str
    monitoramento_ativo: bool
    observacoes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProcessoListResponse(BaseModel):
    items: list[ProcessoResponse]
    total: int
    skip: int
    limit: int
