"""Serviço de autenticação: hash de senha (bcrypt), JWT (HS256)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

# bcrypt aceita no máximo 72 bytes; senhas maiores são truncadas deterministicamente.
_BCRYPT_MAX_BYTES = 72


def _to_bytes(password: str) -> bytes:
    data = password.encode("utf-8")
    return data[:_BCRYPT_MAX_BYTES]


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(_to_bytes(plain), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bytes(plain), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(subject: str, extra_claims: Optional[dict] = None) -> str:
    """Gera um access_token JWT com ``sub`` = id do usuário."""
    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(hours=settings.jwt_access_token_hours),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decodifica um JWT válido. Retorna None se inválido/expirado."""
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
