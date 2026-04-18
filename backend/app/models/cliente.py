"""Modelo Cliente: empresa que emite NFS-e no GISS Maceió."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, index=True, nullable=False)
    inscricao_municipal: Mapped[str] = mapped_column(String(15), nullable=False)
    razao_social: Mapped[str] = mapped_column(String(150), nullable=False)
    nome_fantasia: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)

    cert_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cert_senha_enc: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    cert_validade: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cert_cnpj: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
    cert_cn: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    consultas = relationship("Consulta", back_populates="cliente", cascade="all, delete-orphan")
    nfses = relationship("NfseXml", back_populates="cliente", cascade="all, delete-orphan")
    agendamentos = relationship("Agendamento", back_populates="cliente", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Cliente {self.cnpj} — {self.razao_social}>"
