"""Roteadores FastAPI do CUBO Captura."""
from app.routers import agendamentos, alertas, clientes, consultas, dashboard, nfse

__all__ = ["clientes", "consultas", "nfse", "dashboard", "agendamentos", "alertas"]
