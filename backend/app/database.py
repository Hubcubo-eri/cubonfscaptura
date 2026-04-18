"""Configuração da engine SQLAlchemy e sessão do banco."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos ORM."""


def get_db():
    """Dependency injection para FastAPI fornecendo uma sessão do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Cria as tabelas no banco (para dev/SQLite; em prod, usar Alembic)."""
    # Importar todos os modelos para que o Base.metadata seja populado
    from app.models import agendamento, alerta, certificado, cliente, consulta, nfse, usuario  # noqa: F401

    Base.metadata.create_all(bind=engine)
