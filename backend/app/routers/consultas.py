"""Endpoints para disparar e consultar o histórico de consultas ao GISS."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Consulta
from app.schemas.consulta import ConsultaCreate, ConsultaOut, ConsultaResumo
from app.services.consulta import ConsultaService

router = APIRouter(prefix="/api/consultas", tags=["consultas"])


@router.post("", response_model=ConsultaResumo)
def executar_consulta(payload: ConsultaCreate, db: Session = Depends(get_db)) -> ConsultaResumo:
    try:
        return ConsultaService(db).executar(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("", response_model=List[ConsultaOut])
def listar_consultas(
    cliente_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[ConsultaOut]:
    query = db.query(Consulta)
    if cliente_id:
        query = query.filter(Consulta.cliente_id == cliente_id)
    return query.order_by(Consulta.created_at.desc()).limit(limit).all()


@router.get("/{consulta_id}", response_model=ConsultaOut)
def obter_consulta(consulta_id: str, db: Session = Depends(get_db)) -> ConsultaOut:
    consulta = db.get(Consulta, consulta_id)
    if consulta is None:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    return consulta


@router.get("/{consulta_id}/log")
def log_consulta(consulta_id: str, db: Session = Depends(get_db)) -> dict:
    consulta = db.get(Consulta, consulta_id)
    if consulta is None:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    return {
        "consulta_id": consulta.id,
        "status": consulta.status,
        "xml_request": consulta.xml_request,
        "xml_response_sample": consulta.xml_response_sample,
        "erro_mensagem": consulta.erro_mensagem,
        "duracao_ms": consulta.duracao_ms,
    }
