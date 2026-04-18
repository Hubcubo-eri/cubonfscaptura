"""Task Celery para execução de consultas agendadas.

Implementação inicial: carrega os agendamentos ativos e dispara consultas com
período retroativo configurado. Requer Redis rodando.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

from celery import Celery

from app.config import get_settings
from app.database import SessionLocal
from app.models import Agendamento, TipoConsulta
from app.schemas.consulta import ConsultaCreate, ConsultaParametros
from app.services.consulta import ConsultaService

settings = get_settings()
celery_app = Celery("cubo_captura", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_default_queue = "cubo_captura"

logger = logging.getLogger(__name__)


@celery_app.task(name="cubo_captura.executar_agendamentos")
def executar_agendamentos_ativos() -> dict:
    """Percorre agendamentos ativos e dispara consultas por período de emissão."""
    db = SessionLocal()
    resultados = []
    try:
        agendamentos = db.query(Agendamento).filter(Agendamento.ativo.is_(True)).all()
        hoje = date.today()

        for ag in agendamentos:
            data_final = hoje
            data_inicial = hoje - timedelta(days=ag.periodo_retroativo_dias)
            payload = ConsultaCreate(
                cliente_id=ag.cliente_id,
                tipo=TipoConsulta.periodo_emissao,
                parametros=ConsultaParametros(data_inicial=data_inicial, data_final=data_final),
            )
            try:
                resumo = ConsultaService(db).executar(payload)
                ag.ultima_execucao = resumo.iniciado_em if hasattr(resumo, "iniciado_em") else None
                db.commit()
                resultados.append({"agendamento_id": ag.id, "ok": True, "novos": resumo.novos_xmls})
            except Exception as e:
                logger.exception("Falha ao executar agendamento %s", ag.id)
                resultados.append({"agendamento_id": ag.id, "ok": False, "erro": str(e)})
    finally:
        db.close()

    return {"total": len(resultados), "resultados": resultados}
