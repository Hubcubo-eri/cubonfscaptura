"""Testes de autenticação JWT: login, /me, guard nos endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import create_app
from app.models import Usuario
from app.services.auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


# ============================================================= serviço puro
def test_hash_e_verify_password():
    h = hash_password("minhasenha")
    assert h != "minhasenha"
    assert verify_password("minhasenha", h) is True
    assert verify_password("errada", h) is False


def test_verify_password_com_hash_invalido_retorna_false():
    assert verify_password("x", "nao-eh-hash-bcrypt") is False


def test_create_decode_token_roundtrip():
    token = create_access_token(subject="user-123", extra_claims={"admin": True})
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["admin"] is True


def test_decode_token_invalido_retorna_none():
    assert decode_token("nao-e-um-jwt") is None


# ============================================================= integração
@pytest.fixture
def client_app(tmp_path, monkeypatch):
    db_path = tmp_path / "auth.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setenv("XML_STORAGE_PATH", str(tmp_path / "xmls"))
    monkeypatch.setenv("CERT_STORAGE_PATH", str(tmp_path / "certs"))

    with TestingSessionLocal() as s:
        s.add(
            Usuario(
                email="admin@cubosaude.com.br",
                nome="Admin",
                password_hash=hash_password("admin-secret"),
                admin=True,
                ativo=True,
            )
        )
        s.add(
            Usuario(
                email="user@cubosaude.com.br",
                nome="User",
                password_hash=hash_password("user-secret"),
                admin=False,
                ativo=True,
            )
        )
        s.add(
            Usuario(
                email="inativo@cubosaude.com.br",
                nome="Inativo",
                password_hash=hash_password("inativo-secret"),
                admin=False,
                ativo=False,
            )
        )
        s.commit()

    app = create_app()

    def override_db():
        s = TestingSessionLocal()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c
    engine.dispose()


def test_login_sucesso_retorna_token(client_app):
    r = client_app.post(
        "/api/auth/login",
        data={"username": "admin@cubosaude.com.br", "password": "admin-secret"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_login_senha_errada_401(client_app):
    r = client_app.post(
        "/api/auth/login",
        data={"username": "admin@cubosaude.com.br", "password": "errada"},
    )
    assert r.status_code == 401


def test_login_email_nao_existe_401(client_app):
    r = client_app.post(
        "/api/auth/login",
        data={"username": "nao@existe.com", "password": "x"},
    )
    assert r.status_code == 401


def test_login_usuario_inativo_403(client_app):
    r = client_app.post(
        "/api/auth/login",
        data={"username": "inativo@cubosaude.com.br", "password": "inativo-secret"},
    )
    assert r.status_code == 403


def test_me_sem_token_401(client_app):
    r = client_app.get("/api/auth/me")
    assert r.status_code == 401


def test_me_com_token_valido(client_app):
    login = client_app.post(
        "/api/auth/login",
        data={"username": "user@cubosaude.com.br", "password": "user-secret"},
    )
    token = login.json()["access_token"]

    r = client_app.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "user@cubosaude.com.br"
    assert data["admin"] is False


def test_endpoint_protegido_sem_token_401(client_app):
    r = client_app.get("/api/clientes")
    assert r.status_code == 401


def test_endpoint_protegido_com_token_200(client_app):
    login = client_app.post(
        "/api/auth/login",
        data={"username": "user@cubosaude.com.br", "password": "user-secret"},
    )
    token = login.json()["access_token"]
    r = client_app.get("/api/clientes", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_health_eh_publico(client_app):
    r = client_app.get("/api/health")
    assert r.status_code == 200


def test_criar_usuario_requer_admin(client_app):
    login = client_app.post(
        "/api/auth/login",
        data={"username": "user@cubosaude.com.br", "password": "user-secret"},
    )
    token = login.json()["access_token"]

    r = client_app.post(
        "/api/auth/usuarios",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "novo@cubosaude.com.br", "nome": "Novo", "password": "senha1234"},
    )
    assert r.status_code == 403


def test_admin_cria_usuario(client_app):
    login = client_app.post(
        "/api/auth/login",
        data={"username": "admin@cubosaude.com.br", "password": "admin-secret"},
    )
    token = login.json()["access_token"]

    r = client_app.post(
        "/api/auth/usuarios",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "novo@cubosaude.com.br", "nome": "Novo", "password": "senha1234"},
    )
    assert r.status_code == 201
    assert r.json()["email"] == "novo@cubosaude.com.br"
