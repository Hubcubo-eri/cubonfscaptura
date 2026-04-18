"""Endpoints de autenticação: login, /me, gestão de usuários (admin)."""
from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models import Usuario
from app.schemas.auth import Token, UsuarioCreate, UsuarioOut
from app.services.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Login OAuth2 password flow (username=email, password)."""
    user = db.query(Usuario).filter(Usuario.email == form.username.lower()).one_or_none()
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.ativo:
        raise HTTPException(status_code=403, detail="Usuário desativado")

    settings = get_settings()
    token = create_access_token(subject=user.id, extra_claims={"email": user.email, "admin": user.admin})
    user.ultimo_login = datetime.utcnow()
    db.commit()

    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_hours * 3600,
    )


@router.get("/me", response_model=UsuarioOut)
def me(user: Usuario = Depends(get_current_user)) -> UsuarioOut:
    return user


# ---------------------------------------------------------- gestão (admin)
@router.get("/usuarios", response_model=List[UsuarioOut])
def listar_usuarios(
    _: Usuario = Depends(require_admin), db: Session = Depends(get_db)
) -> List[UsuarioOut]:
    return db.query(Usuario).order_by(Usuario.created_at.desc()).all()


@router.post("/usuarios", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    payload: UsuarioCreate,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UsuarioOut:
    email = payload.email.lower()
    if db.query(Usuario).filter(Usuario.email == email).one_or_none():
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")

    user = Usuario(
        email=email,
        nome=payload.nome,
        password_hash=hash_password(payload.password),
        admin=payload.admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
