"""Schemas Pydantic para NFS-e."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NfseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cliente_id: str
    consulta_id: Optional[str]
    numero_nfse: str
    codigo_verificacao: Optional[str]
    data_emissao: Optional[datetime]
    competencia: Optional[date]
    valor_servicos: Optional[Decimal]
    valor_iss: Optional[Decimal]
    valor_liquido: Optional[Decimal]
    cnpj_prestador: Optional[str]
    cnpj_tomador: Optional[str]
    razao_social_tomador: Optional[str]
    item_lista_servico: Optional[str]
    status_nfse: int
    xml_path: str
    xml_hash: str
    created_at: datetime


class NfseStats(BaseModel):
    total_nfse: int
    total_valor_servicos: Decimal
    total_valor_iss: Decimal
    total_valor_liquido: Decimal
    total_canceladas: int
    por_cliente: list[dict]
