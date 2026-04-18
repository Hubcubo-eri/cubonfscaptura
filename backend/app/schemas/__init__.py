"""Schemas Pydantic para request/response."""
from app.schemas.agendamento import AgendamentoCreate, AgendamentoOut, AgendamentoUpdate
from app.schemas.cliente import (
    CertificadoInfo,
    ClienteCreate,
    ClienteOut,
    ClienteUpdate,
)
from app.schemas.consulta import ConsultaCreate, ConsultaOut, ConsultaResumo
from app.schemas.nfse import NfseOut, NfseStats

__all__ = [
    "ClienteCreate",
    "ClienteUpdate",
    "ClienteOut",
    "CertificadoInfo",
    "ConsultaCreate",
    "ConsultaOut",
    "ConsultaResumo",
    "NfseOut",
    "NfseStats",
    "AgendamentoCreate",
    "AgendamentoUpdate",
    "AgendamentoOut",
]
