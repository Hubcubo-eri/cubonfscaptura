"""Schemas Pydantic para Agendamento."""
from __future__ import annotations

from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.agendamento import TipoAgendamento


class AgendamentoBase(BaseModel):
    cliente_id: str
    tipo: TipoAgendamento
    dia_execucao: Optional[int] = Field(None, ge=0, le=31)
    hora_execucao: time
    periodo_retroativo_dias: int = Field(default=30, ge=1, le=365)
    ativo: bool = True


class AgendamentoCreate(AgendamentoBase):
    pass


class AgendamentoUpdate(BaseModel):
    tipo: Optional[TipoAgendamento] = None
    dia_execucao: Optional[int] = None
    hora_execucao: Optional[time] = None
    periodo_retroativo_dias: Optional[int] = None
    ativo: Optional[bool] = None


class AgendamentoOut(AgendamentoBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ultima_execucao: Optional[datetime]
    created_at: datetime
