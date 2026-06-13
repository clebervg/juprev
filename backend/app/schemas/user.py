import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    # Senha validada: mín. 8 chars, pelo menos 1 maiúscula e 1 número.
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Senha deve conter ao menos uma letra maiúscula.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve conter ao menos um número.")
        return v


class UserResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime

    # LGPD: hashed_password NUNCA é exposto na resposta.
    model_config = {"from_attributes": True}
