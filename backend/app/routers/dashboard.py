"""Endpoints que alimentam o painel principal do frontend."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cliente, Consulta, NfseXml, StatusConsulta

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def stats(db: Session = Depends(get_db)) -> dict:
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)

    total_clientes = db.query(Cliente).count()
    clientes_ativos = db.query(Cliente).filter(Cliente.ativo.is_(True)).count()
    total_nfse = db.query(NfseXml).count()
    nfse_mes = db.query(NfseXml).filter(NfseXml.competencia >= inicio_mes).count()
    valor_mes = (
        db.query(func.coalesce(func.sum(NfseXml.valor_servicos), 0))
        .filter(NfseXml.competencia >= inicio_mes)
        .scalar()
        or 0
    )

    ultima_semana = datetime.utcnow() - timedelta(days=7)
    consultas_semana = db.query(Consulta).filter(Consulta.created_at >= ultima_semana).count()
    consultas_erro_semana = (
        db.query(Consulta)
        .filter(Consulta.created_at >= ultima_semana, Consulta.status == StatusConsulta.erro)
        .count()
    )

    # Certificados vencendo em <=30 dias
    limite = hoje + timedelta(days=30)
    certs_vencendo = (
        db.query(Cliente)
        .filter(Cliente.cert_validade.isnot(None), Cliente.cert_validade <= limite)
        .count()
    )

    return {
        "total_clientes": total_clientes,
        "clientes_ativos": clientes_ativos,
        "total_nfse": total_nfse,
        "nfse_mes_atual": nfse_mes,
        "valor_mes_atual": float(valor_mes),
        "consultas_semana": consultas_semana,
        "consultas_erro_semana": consultas_erro_semana,
        "certificados_vencendo_30d": certs_vencendo,
    }


@router.get("/recentes")
def recentes(db: Session = Depends(get_db)) -> list[dict]:
    rows = (
        db.query(Consulta, Cliente)
        .join(Cliente, Cliente.id == Consulta.cliente_id)
        .order_by(Consulta.created_at.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "consulta_id": c.id,
            "cliente": cli.razao_social,
            "cnpj": cli.cnpj,
            "tipo": c.tipo.value,
            "status": c.status.value,
            "total_notas": c.total_notas,
            "duracao_ms": c.duracao_ms,
            "criado_em": c.created_at.isoformat(),
        }
        for c, cli in rows
    ]


@router.get("/certificados")
def certificados_status(db: Session = Depends(get_db)) -> list[dict]:
    hoje = date.today()
    clientes = (
        db.query(Cliente)
        .filter(Cliente.cert_validade.isnot(None))
        .order_by(Cliente.cert_validade.asc())
        .all()
    )
    resultado = []
    for cli in clientes:
        dias = (cli.cert_validade - hoje).days if cli.cert_validade else None
        resultado.append(
            {
                "cliente_id": cli.id,
                "razao_social": cli.razao_social,
                "cnpj": cli.cnpj,
                "cert_cn": cli.cert_cn,
                "validade": cli.cert_validade.isoformat() if cli.cert_validade else None,
                "dias_para_vencer": dias,
                "status": _cert_status(dias),
            }
        )
    return resultado


def _cert_status(dias: int | None) -> str:
    if dias is None:
        return "desconhecido"
    if dias < 0:
        return "vencido"
    if dias <= 30:
        return "atencao"
    return "ok"
