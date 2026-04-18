"""Endpoints CRUD de clientes + upload de certificado."""
from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Cliente
from app.schemas.cliente import CertificadoInfo, ClienteCreate, ClienteOut, ClienteUpdate
from app.services.certificado import CertificadoService
from app.services.crypto import encrypt_secret

router = APIRouter(prefix="/api/clientes", tags=["clientes"])


@router.get("", response_model=List[ClienteOut])
def listar_clientes(db: Session = Depends(get_db)) -> List[ClienteOut]:
    return db.query(Cliente).order_by(Cliente.razao_social).all()


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def criar_cliente(payload: ClienteCreate, db: Session = Depends(get_db)) -> ClienteOut:
    existente = db.query(Cliente).filter(Cliente.cnpj == payload.cnpj).one_or_none()
    if existente:
        raise HTTPException(status_code=409, detail=f"Cliente com CNPJ {payload.cnpj} já cadastrado")

    cliente = Cliente(**payload.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.get("/{cliente_id}", response_model=ClienteOut)
def obter_cliente(cliente_id: str, db: Session = Depends(get_db)) -> ClienteOut:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente


@router.put("/{cliente_id}", response_model=ClienteOut)
def atualizar_cliente(cliente_id: str, payload: ClienteUpdate, db: Session = Depends(get_db)) -> ClienteOut:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_cliente(cliente_id: str, db: Session = Depends(get_db)) -> None:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    db.delete(cliente)
    db.commit()


# ------------------------------------------------------------- certificado
@router.post("/{cliente_id}/certificado", response_model=CertificadoInfo)
async def upload_certificado(
    cliente_id: str,
    senha: str = Form(..., description="Senha do .pfx"),
    arquivo: UploadFile = File(..., description="Arquivo de certificado .pfx/.p12"),
    db: Session = Depends(get_db),
) -> CertificadoInfo:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    if not arquivo.filename or not arquivo.filename.lower().endswith((".pfx", ".p12")):
        raise HTTPException(status_code=400, detail="Envie um arquivo .pfx ou .p12")

    conteudo = await arquivo.read()
    if len(conteudo) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo maior que 5MB")

    try:
        info = CertificadoService.extract_info(conteudo, senha)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha ao ler certificado: {e}") from e

    settings = get_settings()
    dest = Path(settings.cert_storage_path) / f"{cliente.cnpj}_{info.hash_sha256[:12]}.pfx"
    CertificadoService.save_pfx(conteudo, dest)

    cliente.cert_path = str(dest)
    cliente.cert_senha_enc = encrypt_secret(senha)
    cliente.cert_validade = info.validade_fim
    cliente.cert_cnpj = info.cnpj
    cliente.cert_cn = info.cn
    db.commit()

    return CertificadoInfo(
        cn=info.cn,
        cnpj=info.cnpj,
        validade_inicio=info.validade_inicio,
        validade_fim=info.validade_fim,
        dias_para_vencer=info.dias_para_vencer,
        vencido=info.vencido,
    )


@router.get("/{cliente_id}/certificado", response_model=CertificadoInfo)
def info_certificado(cliente_id: str, db: Session = Depends(get_db)) -> CertificadoInfo:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    if not cliente.cert_path:
        raise HTTPException(status_code=404, detail="Cliente não possui certificado cadastrado")

    from datetime import date

    dias = None
    if cliente.cert_validade:
        dias = (cliente.cert_validade - date.today()).days

    return CertificadoInfo(
        cn=cliente.cert_cn,
        cnpj=cliente.cert_cnpj,
        validade_inicio=None,
        validade_fim=cliente.cert_validade,
        dias_para_vencer=dias,
        vencido=bool(cliente.cert_validade and cliente.cert_validade < date.today()),
    )
