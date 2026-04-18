"""Modelo Consulta: log de cada chamada ao GISS."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class TipoConsulta(str, enum.Enum):
    periodo_emissao = "periodo_emissao"
    periodo_competencia = "periodo_competencia"
    faixa = "faixa"
    rps = "rps"


class StatusConsulta(str, enum.Enum):
    pendente = "pendente"
    processando = "processando"
    sucesso = "sucesso"
    erro = "erro"


class Consulta(Base):
    __tablename__ = "consultas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    cliente_id: Mapped[str] = mapped_column(String(36), ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)

    tipo: Mapped[TipoConsulta] = mapped_column(Enum(TipoConsulta, native_enum=False), nullable=False)
    parametros: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    metodo_ws: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    status: Mapped[StatusConsulta] = mapped_column(
        Enum(StatusConsulta, native_enum=False), default=StatusConsulta.pendente, nullable=False
    )
    total_notas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_paginas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    erro_mensagem: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    xml_request: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    xml_response_sample: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duracao_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    iniciado_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finalizado_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    cliente = relationship("Cliente", back_populates="consultas")
    nfses = relationship("NfseXml", back_populates="consulta")
