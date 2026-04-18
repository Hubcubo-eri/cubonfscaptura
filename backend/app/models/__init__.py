"""Modelos SQLAlchemy do CUBO Captura."""
from app.models.agendamento import Agendamento, TipoAgendamento
from app.models.alerta import Alerta
from app.models.certificado import Certificado
from app.models.cliente import Cliente
from app.models.consulta import Consulta, StatusConsulta, TipoConsulta
from app.models.nfse import NfseXml

__all__ = [
    "Cliente",
    "Certificado",
    "Consulta",
    "TipoConsulta",
    "StatusConsulta",
    "NfseXml",
    "Agendamento",
    "TipoAgendamento",
    "Alerta",
]
