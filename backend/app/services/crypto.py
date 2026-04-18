"""Criptografia simétrica para proteger senhas de certificados em repouso."""
from __future__ import annotations

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings


def _derive_key(master_key: str) -> bytes:
    """Deriva uma chave AES-256 a partir da master key via SHA-256."""
    return hashlib.sha256(master_key.encode("utf-8")).digest()


def encrypt_secret(plaintext: str) -> str:
    """Cifra uma string com AES-256-GCM. Retorna base64(nonce + ciphertext+tag)."""
    settings = get_settings()
    key = _derive_key(settings.master_key)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt_secret(blob: str) -> str:
    """Decifra uma string previamente criptografada com encrypt_secret."""
    settings = get_settings()
    key = _derive_key(settings.master_key)
    raw = base64.b64decode(blob.encode("ascii"))
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, associated_data=None).decode("utf-8")
