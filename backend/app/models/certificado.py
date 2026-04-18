"""Modelo Certificado: histórico de certificados A1 (.pfx) dos clientes."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Certificado(Base):
    __tablename__ = "certificados"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    cliente_id: Mapped[str] = mapped_column(String(36), ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)

    path: Mapped[str] = mapped_column(String(255), nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    cn: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cnpj_certificado: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
    validade_inicio: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    validade_fim: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    cliente = relationship("Cliente")
