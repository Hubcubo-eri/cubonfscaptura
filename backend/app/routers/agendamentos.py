"""Endpoints CRUD de agendamentos de consulta automática."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Agendamento
from app.schemas.agendamento import AgendamentoCreate, AgendamentoOut, AgendamentoUpdate

router = APIRouter(prefix="/api/agendamentos", tags=["agendamentos"])


@router.get("", response_model=List[AgendamentoOut])
def listar(db: Session = Depends(get_db)) -> List[AgendamentoOut]:
    return db.query(Agendamento).order_by(Agendamento.created_at.desc()).all()


@router.post("", response_model=AgendamentoOut, status_code=status.HTTP_201_CREATED)
def criar(payload: AgendamentoCreate, db: Session = Depends(get_db)) -> AgendamentoOut:
    agendamento = Agendamento(**payload.model_dump())
    db.add(agendamento)
    db.commit()
    db.refresh(agendamento)
    return agendamento


@router.put("/{agendamento_id}", response_model=AgendamentoOut)
def atualizar(agendamento_id: str, payload: AgendamentoUpdate, db: Session = Depends(get_db)) -> AgendamentoOut:
    agendamento = db.get(Agendamento, agendamento_id)
    if agendamento is None:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(agendamento, campo, valor)
    db.commit()
    db.refresh(agendamento)
    return agendamento


@router.delete("/{agendamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar(agendamento_id: str, db: Session = Depends(get_db)) -> None:
    agendamento = db.get(Agendamento, agendamento_id)
    if agendamento is None:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    db.delete(agendamento)
    db.commit()
