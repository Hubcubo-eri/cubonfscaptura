"""Endpoints para listar e marcar alertas como resolvidos."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alerta
from app.schemas.alerta import AlertaOut

router = APIRouter(prefix="/api/alertas", tags=["alertas"])


@router.get("", response_model=List[AlertaOut])
def listar(
    tipo: Optional[str] = Query(None),
    apenas_abertos: bool = Query(True),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[AlertaOut]:
    query = db.query(Alerta)
    if tipo:
        query = query.filter(Alerta.tipo == tipo)
    if apenas_abertos:
        query = query.filter(Alerta.resolvido.is_(False))
    return query.order_by(Alerta.created_at.desc()).limit(limit).all()


@router.post("/{alerta_id}/resolver", response_model=AlertaOut)
def resolver(alerta_id: str, db: Session = Depends(get_db)) -> AlertaOut:
    alerta = db.get(Alerta, alerta_id)
    if alerta is None:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    alerta.resolvido = True
    alerta.resolvido_em = datetime.utcnow()
    db.commit()
    db.refresh(alerta)
    return alerta
