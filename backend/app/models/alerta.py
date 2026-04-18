"""Modelo Alerta: eventos operacionais persistidos (cert vencendo, falhas, etc.)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Alerta(Base):
    __tablename__ = "alertas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), default="warning", nullable=False)
    mensagem: Mapped[str] = mapped_column(String(500), nullable=False)
    meta: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    resolvido: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolvido_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
