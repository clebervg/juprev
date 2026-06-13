import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    cnpj: str = Field(..., pattern=r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$")


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    cnpj: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
