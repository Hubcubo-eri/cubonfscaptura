"""Modelo Agendamento: consultas automáticas recorrentes."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, time
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, SmallInteger, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class TipoAgendamento(str, enum.Enum):
    diario = "diario"
    semanal = "semanal"
    mensal = "mensal"


class Agendamento(Base):
    __tablename__ = "agendamentos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    cliente_id: Mapped[str] = mapped_column(String(36), ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)

    tipo: Mapped[TipoAgendamento] = mapped_column(Enum(TipoAgendamento, native_enum=False), nullable=False)
    dia_execucao: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    hora_execucao: Mapped[time] = mapped_column(Time, nullable=False)
    periodo_retroativo_dias: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ultima_execucao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    cliente = relationship("Cliente", back_populates="agendamentos")
