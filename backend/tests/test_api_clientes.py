"""Testes de ponta (TestClient) dos endpoints REST de clientes e dashboard."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient com banco SQLite dedicado e storage em tmp_path."""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    monkeypatch.setenv("XML_STORAGE_PATH", str(tmp_path / "xmls"))
    monkeypatch.setenv("CERT_STORAGE_PATH", str(tmp_path / "certs"))

    app = create_app()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    engine.dispose()


# =================================================================== clientes
def test_listar_clientes_vazio(client):
    r = client.get("/api/clientes")
    assert r.status_code == 200
    assert r.json() == []


def test_criar_cliente(client):
    payload = {
        "cnpj": "12345678000199",
        "inscricao_municipal": "998877",
        "razao_social": "Cubo Teste LTDA",
        "nome_fantasia": "Cubo",
    }
    r = client.post("/api/clientes", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["cnpj"] == "12345678000199"
    assert data["razao_social"] == "Cubo Teste LTDA"
    assert data["ativo"] is True
    assert "id" in data


def test_criar_cliente_cnpj_formatado_e_normalizado(client):
    r = client.post(
        "/api/clientes",
        json={
            "cnpj": "12.345.678/0001-99",
            "inscricao_municipal": "998877",
            "razao_social": "Cubo LTDA",
        },
    )
    assert r.status_code == 201
    assert r.json()["cnpj"] == "12345678000199"


def test_criar_cliente_cnpj_invalido(client):
    r = client.post(
        "/api/clientes",
        json={"cnpj": "123", "inscricao_municipal": "1", "razao_social": "X"},
    )
    assert r.status_code == 422


def test_criar_cliente_duplicado_conflito(client):
    payload = {
        "cnpj": "12345678000199",
        "inscricao_municipal": "998877",
        "razao_social": "Cubo",
    }
    client.post("/api/clientes", json=payload)
    r = client.post("/api/clientes", json=payload)
    assert r.status_code == 409


def test_atualizar_cliente(client):
    r = client.post(
        "/api/clientes",
        json={"cnpj": "12345678000199", "inscricao_municipal": "1", "razao_social": "Original"},
    )
    cid = r.json()["id"]

    r = client.put(f"/api/clientes/{cid}", json={"razao_social": "Atualizada", "ativo": False})
    assert r.status_code == 200
    assert r.json()["razao_social"] == "Atualizada"
    assert r.json()["ativo"] is False


def test_deletar_cliente(client):
    r = client.post(
        "/api/clientes",
        json={"cnpj": "12345678000199", "inscricao_municipal": "1", "razao_social": "Original"},
    )
    cid = r.json()["id"]

    r = client.delete(f"/api/clientes/{cid}")
    assert r.status_code == 204
    r = client.get(f"/api/clientes/{cid}")
    assert r.status_code == 404


def test_obter_cliente_inexistente(client):
    r = client.get("/api/clientes/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_info_certificado_sem_cert_retorna_404(client):
    r = client.post(
        "/api/clientes",
        json={"cnpj": "12345678000199", "inscricao_municipal": "1", "razao_social": "Cubo"},
    )
    cid = r.json()["id"]
    r = client.get(f"/api/clientes/{cid}/certificado")
    assert r.status_code == 404


# ================================================================== dashboard
def test_dashboard_stats_vazio(client):
    r = client.get("/api/dashboard/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["total_clientes"] == 0
    assert data["total_nfse"] == 0
    assert data["consultas_semana"] == 0


def test_dashboard_stats_com_cliente(client):
    client.post(
        "/api/clientes",
        json={"cnpj": "12345678000199", "inscricao_municipal": "1", "razao_social": "Cubo"},
    )
    r = client.get("/api/dashboard/stats")
    data = r.json()
    assert data["total_clientes"] == 1
    assert data["clientes_ativos"] == 1


def test_dashboard_recentes_vazio(client):
    r = client.get("/api/dashboard/recentes")
    assert r.status_code == 200
    assert r.json() == []


def test_dashboard_certificados_vazio(client):
    r = client.get("/api/dashboard/certificados")
    assert r.status_code == 200
    assert r.json() == []


def test_health_endpoint(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
