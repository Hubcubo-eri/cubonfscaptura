"""Endpoints para listar, baixar e exportar XMLs de NFS-e capturadas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cliente, NfseXml
from app.schemas.nfse import NfseOut, NfseStats
from app.services.storage import StorageService

router = APIRouter(prefix="/api/nfse", tags=["nfse"])


@router.get("", response_model=List[NfseOut])
def listar_nfse(
    cliente_id: Optional[str] = Query(None),
    competencia_inicial: Optional[date] = Query(None),
    competencia_final: Optional[date] = Query(None),
    numero: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> List[NfseOut]:
    query = db.query(NfseXml)
    if cliente_id:
        query = query.filter(NfseXml.cliente_id == cliente_id)
    if competencia_inicial:
        query = query.filter(NfseXml.competencia >= competencia_inicial)
    if competencia_final:
        query = query.filter(NfseXml.competencia <= competencia_final)
    if numero:
        query = query.filter(NfseXml.numero_nfse == numero)
    return query.order_by(NfseXml.data_emissao.desc().nullslast()).limit(limit).all()


@router.get("/stats", response_model=NfseStats)
def stats_nfse(
    cliente_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> NfseStats:
    query = db.query(NfseXml)
    if cliente_id:
        query = query.filter(NfseXml.cliente_id == cliente_id)

    total = query.count()
    soma_servicos = query.with_entities(func.coalesce(func.sum(NfseXml.valor_servicos), 0)).scalar() or 0
    soma_iss = query.with_entities(func.coalesce(func.sum(NfseXml.valor_iss), 0)).scalar() or 0
    soma_liquido = query.with_entities(func.coalesce(func.sum(NfseXml.valor_liquido), 0)).scalar() or 0
    total_canc = query.filter(NfseXml.status_nfse == 2).count()

    por_cliente_rows = (
        db.query(
            Cliente.id,
            Cliente.razao_social,
            Cliente.cnpj,
            func.count(NfseXml.id).label("total"),
            func.coalesce(func.sum(NfseXml.valor_servicos), 0).label("valor"),
        )
        .join(NfseXml, NfseXml.cliente_id == Cliente.id)
        .group_by(Cliente.id, Cliente.razao_social, Cliente.cnpj)
        .order_by(func.count(NfseXml.id).desc())
        .limit(10)
        .all()
    )
    por_cliente = [
        {
            "cliente_id": r.id,
            "razao_social": r.razao_social,
            "cnpj": r.cnpj,
            "total": int(r.total),
            "valor_servicos": float(r.valor),
        }
        for r in por_cliente_rows
    ]

    return NfseStats(
        total_nfse=total,
        total_valor_servicos=Decimal(str(soma_servicos)),
        total_valor_iss=Decimal(str(soma_iss)),
        total_valor_liquido=Decimal(str(soma_liquido)),
        total_canceladas=total_canc,
        por_cliente=por_cliente,
    )


@router.get("/{nfse_id}/xml")
def download_xml(nfse_id: str, db: Session = Depends(get_db)) -> FileResponse:
    nfse = db.get(NfseXml, nfse_id)
    if nfse is None:
        raise HTTPException(status_code=404, detail="NFS-e não encontrada")
    path = Path(nfse.xml_path)
    if not path.exists():
        raise HTTPException(status_code=410, detail="Arquivo XML não disponível no storage")
    return FileResponse(
        path=path,
        media_type="application/xml",
        filename=f"nfse_{nfse.numero_nfse}.xml",
    )


@router.get("/export")
def export_zip(
    cliente_id: Optional[str] = Query(None),
    competencia_inicial: Optional[date] = Query(None),
    competencia_final: Optional[date] = Query(None),
    db: Session = Depends(get_db),
) -> Response:
    query = db.query(NfseXml)
    if cliente_id:
        query = query.filter(NfseXml.cliente_id == cliente_id)
    if competencia_inicial:
        query = query.filter(NfseXml.competencia >= competencia_inicial)
    if competencia_final:
        query = query.filter(NfseXml.competencia <= competencia_final)

    notas = query.all()
    if not notas:
        raise HTTPException(status_code=404, detail="Nenhum XML encontrado para os filtros")

    pares = [
        (
            f"{n.cnpj_prestador or 'xx'}/{(n.competencia.strftime('%Y-%m') if n.competencia else 'sem-comp')}/nfse_{n.numero_nfse}.xml",
            n.xml_path,
        )
        for n in notas
    ]
    zip_bytes = StorageService().build_zip(pares)

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="nfse_export.zip"'},
    )
