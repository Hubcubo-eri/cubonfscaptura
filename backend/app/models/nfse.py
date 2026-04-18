"""Modelo NfseXml: metadados dos XMLs NFS-e capturados."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Date, ForeignKey, Numeric, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class NfseXml(Base):
    __tablename__ = "nfse_xmls"
    __table_args__ = (UniqueConstraint("cliente_id", "numero_nfse", name="uq_nfse_cliente_numero"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    cliente_id: Mapped[str] = mapped_column(String(36), ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    consulta_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("consultas.id", ondelete="SET NULL"), nullable=True
    )

    numero_nfse: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    codigo_verificacao: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    data_emissao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    competencia: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)

    valor_servicos: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    valor_iss: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    valor_liquido: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    cnpj_prestador: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
    cnpj_tomador: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
    razao_social_tomador: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    item_lista_servico: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)

    status_nfse: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)  # 1=Normal, 2=Cancelada
    xml_path: Mapped[str] = mapped_column(String(255), nullable=False)
    xml_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    cliente = relationship("Cliente", back_populates="nfses")
    consulta = relationship("Consulta", back_populates="nfses")
