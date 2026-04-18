"""Schemas Pydantic para Cliente e Certificado."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean_cnpj(v: str) -> str:
    if not v:
        return v
    return "".join(c for c in v if c.isdigit())


class ClienteBase(BaseModel):
    cnpj: str = Field(..., description="CNPJ (apenas dígitos)")
    inscricao_municipal: str = Field(..., max_length=15)
    razao_social: str = Field(..., max_length=150)
    nome_fantasia: Optional[str] = Field(None, max_length=60)
    ativo: bool = True

    @field_validator("cnpj", mode="before")
    @classmethod
    def strip_cnpj(cls, v):
        v = _clean_cnpj(v)
        if len(v) != 14:
            raise ValueError("CNPJ deve conter 14 dígitos")
        return v

    @field_validator("inscricao_municipal", mode="before")
    @classmethod
    def strip_im(cls, v):
        if v is None:
            return v
        return str(v).strip()


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    inscricao_municipal: Optional[str] = None
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    ativo: Optional[bool] = None


class CertificadoInfo(BaseModel):
    cn: Optional[str] = None
    cnpj: Optional[str] = None
    validade_inicio: Optional[date] = None
    validade_fim: Optional[date] = None
    dias_para_vencer: Optional[int] = None
    vencido: bool = False


class ClienteOut(ClienteBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cert_path: Optional[str] = None
    cert_validade: Optional[date] = None
    cert_cnpj: Optional[str] = None
    cert_cn: Optional[str] = None
    created_at: datetime
    updated_at: datetime
