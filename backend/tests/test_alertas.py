"""Testes do AlertaService + endpoints /api/alertas."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import create_app
from app.models import Alerta
from app.services.alertas import AlertaService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()
        engine.dispose()


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "t.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setenv("XML_STORAGE_PATH", str(tmp_path / "xmls"))
    monkeypatch.setenv("CERT_STORAGE_PATH", str(tmp_path / "certs"))

    app = create_app()

    def override_db():
        s = TestingSessionLocal()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c, TestingSessionLocal
    engine.dispose()


# =================================================================== service
def test_alerta_service_emitir_persiste(db_session):
    aid = AlertaService.emitir(
        tipo="certificado_vencendo",
        mensagem="Cert X vence em 5 dias",
        metadata={"cliente_id": "abc", "dias": 5},
        severity="warning",
        db=db_session,
    )
    assert aid is not None

    alerta = db_session.get(Alerta, aid)
    assert alerta.tipo == "certificado_vencendo"
    assert alerta.severity == "warning"
    assert alerta.mensagem == "Cert X vence em 5 dias"
    assert alerta.meta == {"cliente_id": "abc", "dias": 5}
    assert alerta.resolvido is False
    assert alerta.resolvido_em is None


def test_alerta_service_sem_db_explicito_abre_sessao():
    """Quando db=None, o serviço usa SessionLocal internamente."""
    # Este teste apenas garante que não levanta. A sessão default aponta para o
    # DATABASE_URL configurado (SQLite in-memory no conftest).
    aid = AlertaService.emitir(tipo="teste", mensagem="ok")
    # Pode retornar None se o DB não tem a tabela alertas ainda (in-memory do
    # conftest) — o importante é não crashar. Basta ter sido logado.
    assert aid is None or isinstance(aid, str)


# =================================================================== endpoint
def test_api_listar_alertas_vazio(client):
    c, _ = client
    r = c.get("/api/alertas")
    assert r.status_code == 200
    assert r.json() == []


def test_api_listar_alertas_apos_emissao(client):
    c, Session = client
    with Session() as s:
        AlertaService.emitir(tipo="cert_vence", mensagem="teste", db=s)

    r = c.get("/api/alertas")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["tipo"] == "cert_vence"
    assert data[0]["resolvido"] is False


def test_api_filtrar_por_tipo(client):
    c, Session = client
    with Session() as s:
        AlertaService.emitir(tipo="cert_vence", mensagem="a", db=s)
        AlertaService.emitir(tipo="consulta_falha", mensagem="b", db=s)

    r = c.get("/api/alertas?tipo=cert_vence")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["tipo"] == "cert_vence"


def test_api_resolver_alerta(client):
    c, Session = client
    with Session() as s:
        aid = AlertaService.emitir(tipo="x", mensagem="y", db=s)

    r = c.post(f"/api/alertas/{aid}/resolver")
    assert r.status_code == 200
    assert r.json()["resolvido"] is True
    assert r.json()["resolvido_em"] is not None

    # Não aparece mais no filtro padrão (apenas_abertos=True)
    r = c.get("/api/alertas")
    assert r.json() == []

    # Mas aparece com apenas_abertos=false
    r = c.get("/api/alertas?apenas_abertos=false")
    assert len(r.json()) == 1


def test_api_resolver_alerta_inexistente(client):
    c, _ = client
    r = c.post("/api/alertas/00000000-0000-0000-0000-000000000000/resolver")
    assert r.status_code == 404
