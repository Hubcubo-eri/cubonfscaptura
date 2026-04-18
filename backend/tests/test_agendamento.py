"""Testes da janela de execução de agendamentos."""
from __future__ import annotations

from datetime import datetime, time
from types import SimpleNamespace

from app.models import TipoAgendamento
from app.tasks.consulta_agendada import _deveria_executar


def _ag(**kwargs):
    base = dict(
        ativo=True,
        ultima_execucao=None,
        hora_execucao=time(8, 0),
        tipo=TipoAgendamento.diario,
        dia_execucao=None,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def test_diario_dentro_da_janela_executa():
    agora = datetime(2026, 4, 18, 8, 5)
    assert _deveria_executar(_ag(), agora) is True


def test_diario_antes_da_hora_nao_executa():
    agora = datetime(2026, 4, 18, 7, 59)
    assert _deveria_executar(_ag(), agora) is False


def test_diario_fora_da_janela_de_20min_nao_executa():
    agora = datetime(2026, 4, 18, 8, 30)
    assert _deveria_executar(_ag(), agora) is False


def test_ja_executado_hoje_nao_repete():
    ontem_executado = datetime(2026, 4, 18, 8, 0)
    agora = datetime(2026, 4, 18, 8, 10)
    assert _deveria_executar(_ag(ultima_execucao=ontem_executado), agora) is False


def test_executado_ontem_permite_hoje():
    ontem = datetime(2026, 4, 17, 8, 0)
    agora = datetime(2026, 4, 18, 8, 5)
    assert _deveria_executar(_ag(ultima_execucao=ontem), agora) is True


def test_inativo_nunca_executa():
    agora = datetime(2026, 4, 18, 8, 5)
    assert _deveria_executar(_ag(ativo=False), agora) is False


def test_semanal_dia_correto_executa():
    # 2026-04-18 é um sábado = weekday 5
    agora = datetime(2026, 4, 18, 8, 5)
    ag = _ag(tipo=TipoAgendamento.semanal, dia_execucao=5)
    assert _deveria_executar(ag, agora) is True


def test_semanal_dia_errado_nao_executa():
    agora = datetime(2026, 4, 18, 8, 5)
    ag = _ag(tipo=TipoAgendamento.semanal, dia_execucao=0)  # segunda
    assert _deveria_executar(ag, agora) is False


def test_mensal_dia_correto_executa():
    agora = datetime(2026, 4, 18, 8, 5)
    ag = _ag(tipo=TipoAgendamento.mensal, dia_execucao=18)
    assert _deveria_executar(ag, agora) is True


def test_mensal_dia_errado_nao_executa():
    agora = datetime(2026, 4, 18, 8, 5)
    ag = _ag(tipo=TipoAgendamento.mensal, dia_execucao=1)
    assert _deveria_executar(ag, agora) is False
