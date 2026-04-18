"""Schemas Pydantic de autenticação."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    nome: str
    admin: bool
    ativo: bool
    ultimo_login: Optional[datetime] = None
    created_at: datetime


class UsuarioCreate(BaseModel):
    email: EmailStr
    nome: str = Field(..., max_length=150)
    password: str = Field(..., min_length=8)
    admin: bool = False
