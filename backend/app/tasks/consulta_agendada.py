"""Tasks Celery: beat schedule + consultas agendadas + alertas de certificado.

O beat despacha periodicamente duas tasks:

* ``executar_agendamentos_ativos`` — a cada 15 minutos avalia os agendamentos
  e dispara aqueles cuja janela (tipo + dia + hora) caiu dentro do intervalo
  atual e que ainda não foram executados hoje.
* ``verificar_certificados_vencendo`` — uma vez por dia (08:00 UTC) verifica
  certificados A1 que vencem em até 30 dias e registra alertas.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings
from app.database import SessionLocal
from app.models import Agendamento, Cliente, TipoAgendamento, TipoConsulta
from app.schemas.consulta import ConsultaCreate, ConsultaParametros
from app.services.alertas import AlertaService
from app.services.consulta import ConsultaService

logger = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery("cubo_captura", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_default_queue="cubo_captura",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "executar-agendamentos-ativos": {
            "task": "cubo_captura.executar_agendamentos",
            "schedule": crontab(minute="*/15"),
        },
        "verificar-certificados-vencendo": {
            "task": "cubo_captura.verificar_certificados",
            "schedule": crontab(minute=0, hour=8),
        },
    },
)


# ---------------------------------------------------------------- utilidades
def _deveria_executar(agendamento: Agendamento, agora: datetime) -> bool:
    """Retorna True se o agendamento caiu na janela atual e ainda não rodou hoje."""
    if not agendamento.ativo:
        return False
    if agendamento.ultima_execucao and agendamento.ultima_execucao.date() == agora.date():
        return False

    hora_ag: time = agendamento.hora_execucao
    hora_atual = agora.time()
    # Janela de 15 minutos após a hora marcada (margem do beat de 15min).
    if hora_atual < hora_ag:
        return False
    delta_min = (hora_atual.hour - hora_ag.hour) * 60 + (hora_atual.minute - hora_ag.minute)
    if delta_min > 20:
        return False

    if agendamento.tipo == TipoAgendamento.diario:
        return True
    if agendamento.tipo == TipoAgendamento.semanal:
        return agendamento.dia_execucao is not None and agora.weekday() == agendamento.dia_execucao
    if agendamento.tipo == TipoAgendamento.mensal:
        return agendamento.dia_execucao is not None and agora.day == agendamento.dia_execucao
    return False


# ------------------------------------------------------------------- tasks
@celery_app.task(name="cubo_captura.executar_agendamentos")
def executar_agendamentos_ativos() -> dict:
    """Dispara consultas para agendamentos que caíram na janela atual."""
    db = SessionLocal()
    resultados = []
    agora = datetime.utcnow()
    hoje = date.today()
    try:
        agendamentos = db.query(Agendamento).filter(Agendamento.ativo.is_(True)).all()
        for ag in agendamentos:
            if not _deveria_executar(ag, agora):
                continue
            data_final = hoje
            data_inicial = hoje - timedelta(days=ag.periodo_retroativo_dias)
            payload = ConsultaCreate(
                cliente_id=ag.cliente_id,
                tipo=TipoConsulta.periodo_emissao,
                parametros=ConsultaParametros(data_inicial=data_inicial, data_final=data_final),
            )
            try:
                resumo = ConsultaService(db).executar(payload)
                ag.ultima_execucao = agora
                db.add(ag)
                db.commit()
                resultados.append(
                    {
                        "agendamento_id": ag.id,
                        "cliente_id": ag.cliente_id,
                        "ok": True,
                        "notas": resumo.total_notas,
                        "novos": resumo.novos_xmls,
                    }
                )
            except Exception as e:
                logger.exception("Falha ao executar agendamento %s", ag.id)
                resultados.append({"agendamento_id": ag.id, "ok": False, "erro": str(e)})
    finally:
        db.close()

    logger.info("Agendamentos processados: %d", len(resultados))
    return {"total": len(resultados), "resultados": resultados}


@celery_app.task(name="cubo_captura.verificar_certificados")
def verificar_certificados_vencendo(dias_alerta: int = 30) -> dict:
    """Registra alertas para certificados A1 que vencem em até ``dias_alerta`` dias."""
    db = SessionLocal()
    alertas = []
    try:
        hoje = date.today()
        limite = hoje + timedelta(days=dias_alerta)
        clientes = (
            db.query(Cliente)
            .filter(
                Cliente.cert_validade.isnot(None),
                Cliente.cert_validade <= limite,
                Cliente.ativo.is_(True),
            )
            .all()
        )
        for cli in clientes:
            dias = (cli.cert_validade - hoje).days if cli.cert_validade else None
            AlertaService.emitir(
                tipo="certificado_vencendo",
                mensagem=(
                    f"Certificado de {cli.razao_social} ({cli.cnpj}) "
                    f"{'vencido' if dias is not None and dias < 0 else f'vence em {dias} dia(s)'}"
                ),
                metadata={
                    "cliente_id": cli.id,
                    "cnpj": cli.cnpj,
                    "validade": cli.cert_validade.isoformat() if cli.cert_validade else None,
                    "dias_para_vencer": dias,
                },
            )
            alertas.append({"cliente_id": cli.id, "cnpj": cli.cnpj, "dias": dias})
    finally:
        db.close()

    logger.info("Certificados alertados: %d", len(alertas))
    return {"total": len(alertas), "alertas": alertas}
