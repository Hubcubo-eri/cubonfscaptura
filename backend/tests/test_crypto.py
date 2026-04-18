"""Testes da criptografia simétrica de senhas de certificado."""
from __future__ import annotations

import pytest

from app.services.crypto import decrypt_secret, encrypt_secret


def test_encrypt_decrypt_roundtrip():
    senha = "senha-super-secreta-do-cert-A1"
    blob = encrypt_secret(senha)
    assert blob != senha
    assert decrypt_secret(blob) == senha


def test_encrypt_produz_outputs_diferentes_por_nonce():
    """Cada chamada de encrypt_secret usa um nonce novo: o blob muda."""
    a = encrypt_secret("x")
    b = encrypt_secret("x")
    assert a != b
    assert decrypt_secret(a) == "x"
    assert decrypt_secret(b) == "x"


def test_decrypt_blob_invalido_levanta():
    with pytest.raises(Exception):
        decrypt_secret("naoEhBase64Valido!!!")


def test_decrypt_com_chave_errada(monkeypatch):
    """Se a master key mudar entre encrypt e decrypt, deve falhar."""
    blob = encrypt_secret("segredo")

    from app.services import crypto
    from app.config import get_settings

    # Invalida o cache de Settings e troca a master key
    get_settings.cache_clear()
    monkeypatch.setenv("MASTER_KEY", "chave-diferente-totalmente-aleatoria-xyz")
    try:
        with pytest.raises(Exception):
            crypto.decrypt_secret(blob)
    finally:
        get_settings.cache_clear()
