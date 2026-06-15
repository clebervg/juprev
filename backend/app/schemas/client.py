import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


# ─── Validadores CPF/NIS ────────────────────────────────────────────────────

def _validate_cpf(cpf: str) -> str:
    digits = re.sub(r"\D", "", cpf)
    if len(digits) != 11 or len(set(digits)) == 1:
        raise ValueError("CPF inválido.")
    for i in range(2):
        total = sum(int(d) * (10 + i - j) for j, d in enumerate(digits[:9 + i]))
        remainder = (total * 10) % 11
        if remainder == 10:
            remainder = 0
        if remainder != int(digits[9 + i]):
            raise ValueError("CPF inválido.")
    return digits


def _validate_nis(nis: str) -> str:
    digits = re.sub(r"\D", "", nis)
    if len(digits) != 11:
        raise ValueError("NIS/PIS/PASEP deve ter 11 dígitos.")
    weights = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(digits[:10], weights))
    remainder = total % 11
    check = 0 if remainder < 2 else 11 - remainder
    if check != int(digits[10]):
        raise ValueError("NIS/PIS/PASEP inválido.")
    return digits


# ─── Dependente ─────────────────────────────────────────────────────────────

class DependenteCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=255)
    cpf: str | None = None
    data_nascimento: date | None = None
    parentesco: Literal["filho", "conjuge", "companheiro", "outros"] | None = None
    e_beneficiario: bool = False
    percentual_dependencia: int | None = Field(None, ge=0, le=100)

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str | None) -> str | None:
        return _validate_cpf(v) if v else None


class DependenteResponse(BaseModel):
    id: uuid.UUID
    nome: str
    cpf: str | None
    data_nascimento: date | None
    parentesco: str | None
    e_beneficiario: bool
    percentual_dependencia: int | None

    model_config = {"from_attributes": True}


# ─── Client ─────────────────────────────────────────────────────────────────

class ClientCreate(BaseModel):
    # Dados pessoais
    nome: str = Field(..., min_length=2, max_length=255)
    cpf: str | None = Field(None, max_length=14)
    rg: str | None = Field(None, max_length=20)
    rg_orgao_expedidor: str | None = Field(None, max_length=10)
    data_nascimento: date | None = None
    nome_mae: str | None = Field(None, max_length=255)
    nome_pai: str | None = Field(None, max_length=255)
    estado_civil: Literal["solteiro", "casado", "divorciado", "viuvo", "uniao_estavel"] | None = None
    genero: Literal["masculino", "feminino", "outro"] | None = None
    nis: str | None = Field(None, max_length=11)
    ctps_numero: str | None = Field(None, max_length=10)
    ctps_serie: str | None = Field(None, max_length=5)
    escolaridade: str | None = Field(None, max_length=50)
    profissao: str | None = Field(None, max_length=100)

    # Contato
    email: str | None = Field(None, max_length=255)
    telefone_celular: str | None = Field(None, max_length=20)
    whatsapp: bool = True
    telefone_fixo: str | None = Field(None, max_length=20)
    contato_emergencia_nome: str | None = Field(None, max_length=255)
    contato_emergencia_telefone: str | None = Field(None, max_length=20)

    # Endereço
    cep: str | None = Field(None, max_length=8)
    logradouro: str | None = Field(None, max_length=255)
    numero: str | None = Field(None, max_length=10)
    complemento: str | None = Field(None, max_length=50)
    bairro: str | None = Field(None, max_length=100)
    cidade: str | None = Field(None, max_length=100)
    uf: str | None = Field(None, max_length=2)

    tipo_residencia: Literal["propria", "alugada", "cedida", "outras"] | None = None
    renda_mensal: Decimal | None = Field(None, ge=0)
    possui_deficiencia: bool = False
    tipo_deficiencia: str | None = Field(None, max_length=100)
    tempo_contribuicao_anos: int | None = Field(None, ge=0, le=50)
    observacoes: str | None = None

    dependentes: list[DependenteCreate] = []

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str | None) -> str | None:
        return _validate_cpf(v) if v else None

    @field_validator("nis")
    @classmethod
    def validate_nis(cls, v: str | None) -> str | None:
        return _validate_nis(v) if v else None

    @model_validator(mode="after")
    def validate_age(self) -> "ClientCreate":
        from datetime import date as date_type
        if self.data_nascimento is None:
            return self
        today = date_type.today()
        age = (today - self.data_nascimento).days // 365
        if age < 16:
            raise ValueError("Cliente deve ter no mínimo 16 anos.")
        return self


class ClientUpdate(BaseModel):
    nome: str | None = Field(None, min_length=2, max_length=255)
    cpf: str | None = Field(None, max_length=14)
    rg: str | None = Field(None, max_length=20)
    rg_orgao_expedidor: str | None = None
    data_nascimento: date | None = None
    nome_mae: str | None = None
    nome_pai: str | None = None
    estado_civil: Literal["solteiro", "casado", "divorciado", "viuvo", "uniao_estavel"] | None = None
    genero: Literal["masculino", "feminino", "outro"] | None = None
    nis: str | None = Field(None, max_length=11)
    ctps_numero: str | None = None
    ctps_serie: str | None = None
    escolaridade: str | None = None
    profissao: str | None = None
    email: str | None = None
    telefone_celular: str | None = None
    whatsapp: bool | None = None
    telefone_fixo: str | None = None
    contato_emergencia_nome: str | None = None
    contato_emergencia_telefone: str | None = None
    cep: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None
    tipo_residencia: Literal["propria", "alugada", "cedida", "outras"] | None = None
    renda_mensal: Decimal | None = None
    possui_deficiencia: bool | None = None
    tipo_deficiencia: str | None = None
    tempo_contribuicao_anos: int | None = None
    observacoes: str | None = None
    # None = não enviado (não toca nos dependentes); [] = enviado vazio (remove todos)
    dependentes: list[DependenteCreate] | None = None

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str | None) -> str | None:
        return _validate_cpf(v) if v else None

    @field_validator("nis")
    @classmethod
    def validate_nis(cls, v: str | None) -> str | None:
        return _validate_nis(v) if v else None


class ClientResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    # Dados pessoais
    nome: str
    cpf: str | None
    rg: str | None
    rg_orgao_expedidor: str | None
    data_nascimento: date | None
    nome_mae: str | None
    nome_pai: str | None
    estado_civil: str | None
    genero: str | None
    nis: str | None
    ctps_numero: str | None
    ctps_serie: str | None
    escolaridade: str | None
    profissao: str | None
    tempo_contribuicao_anos: int | None
    # Contato
    email: str | None
    telefone_celular: str | None
    whatsapp: bool
    telefone_fixo: str | None
    contato_emergencia_nome: str | None
    contato_emergencia_telefone: str | None
    # Endereço
    cep: str | None
    logradouro: str | None
    numero: str | None
    complemento: str | None
    bairro: str | None
    cidade: str | None
    uf: str | None
    tipo_residencia: str | None
    # Dados adicionais
    renda_mensal: float | None
    possui_deficiencia: bool
    tipo_deficiencia: str | None
    observacoes: str | None
    created_at: datetime
    dependentes: list[DependenteResponse] = []

    model_config = {"from_attributes": True}


class ClientListItem(BaseModel):
    """Resposta compacta para listagens — sem dados sensíveis completos."""
    id: uuid.UUID
    nome: str
    cpf_mascarado: str
    telefone_celular: str | None
    cidade: str | None
    uf: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
