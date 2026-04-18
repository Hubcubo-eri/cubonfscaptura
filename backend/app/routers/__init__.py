"""Roteadores FastAPI do CUBO Captura."""
from app.routers import agendamentos, clientes, consultas, dashboard, nfse

__all__ = ["clientes", "consultas", "nfse", "dashboard", "agendamentos"]
