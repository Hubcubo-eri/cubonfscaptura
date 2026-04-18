"""Dependencies do FastAPI: autenticação JWT."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario
from app.services.auth import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Valida o JWT e retorna o Usuario ativo correspondente."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou sessão expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception

    user = db.get(Usuario, payload["sub"])
    if user is None or not user.ativo:
        raise credentials_exception
    return user


def require_admin(user: Usuario = Depends(get_current_user)) -> Usuario:
    if not user.admin:
        raise HTTPException(status_code=403, detail="Requer privilégio de administrador")
    return user
