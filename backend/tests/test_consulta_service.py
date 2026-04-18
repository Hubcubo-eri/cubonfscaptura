"""Testes de integração do ConsultaService (DB em memória + GISS mockado)."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.giss import GISSException
from app.giss.xml_parser import NfseData
from app.models import Cliente, NfseXml, StatusConsulta, TipoConsulta
from app.schemas.consulta import ConsultaCreate, ConsultaParametros
from app.services.consulta import ConsultaService
from app.services.storage import StorageService


# ======================================================================== fixtures
@pytest.fixture
def db_session():
    """Cria um banco SQLite em memória isolado por teste."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def storage(tmp_path):
    """StorageService apontando para tmp_path do pytest."""
    return StorageService(base_path=tmp_path)


@pytest.fixture
def cliente(db_session):
    """Cliente pronto para uso, com cert_path falso (não será lido no mock)."""
    c = Cliente(
        cnpj="12345678000199",
        inscricao_municipal="998877",
        razao_social="Cubo Teste LTDA",
        cert_path="/tmp/fake.pfx",
        cert_senha_enc="fake-encrypted",
        ativo=True,
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


def _mk_nota(numero: str, valor: str = "1000.00", status: int = 1) -> NfseData:
    return NfseData(
        numero=numero,
        codigo_verificacao=f"CV{numero}",
        data_emissao=datetime(2026, 1, 15, 10, 0, 0),
        competencia=date(2026, 1, 1),
        valor_servicos=Decimal(valor),
        valor_iss=Decimal("50.00"),
        valor_liquido=Decimal("950.00"),
        cnpj_prestador="12345678000199",
        im_prestador="998877",
        razao_social_prestador="Cubo Teste LTDA",
        cnpj_tomador="98765432000111",
        razao_social_tomador="Tomador Exemplo SA",
        item_lista_servico="04.08",
        status=status,
        xml_completo=f'<?xml version="1.0"?><CompNfse><n>{numero}</n></CompNfse>',
    )


@contextmanager
def _mock_giss_client(notas: list[NfseData]):
    """Substitui build_client_for_cliente por um GISSClient fake."""

    class FakeClient:
        def consultar_todas_paginas(self, metodo_nome, **kwargs):
            return notas

        def close(self):
            pass

    @contextmanager
    def fake_builder(cliente):
        yield FakeClient()

    with patch("app.services.consulta.build_client_for_cliente", fake_builder):
        yield


# ============================================================================ tests
def test_consulta_sucesso_persiste_nfse_e_xmls(db_session, cliente, storage):
    notas = [_mk_nota("00000001"), _mk_nota("00000002")]
    payload = ConsultaCreate(
        cliente_id=cliente.id,
        tipo=TipoConsulta.periodo_emissao,
        parametros=ConsultaParametros(data_inicial=date(2026, 1, 1), data_final=date(2026, 1, 31)),
    )

    with _mock_giss_client(notas):
        resumo = ConsultaService(db_session, storage=storage).executar(payload)

    assert resumo.status == StatusConsulta.sucesso
    assert resumo.total_notas == 2
    assert resumo.novos_xmls == 2
    assert resumo.erro_mensagem is None
    assert resumo.duracao_ms is not None

    persistidas = db_session.query(NfseXml).filter(NfseXml.cliente_id == cliente.id).all()
    assert len(persistidas) == 2
    numeros = {n.numero_nfse for n in persistidas}
    assert numeros == {"00000001", "00000002"}

    for nota in persistidas:
        path = Path(nota.xml_path)
        assert path.exists()
        assert "2026-01" in str(path)
        assert cliente.cnpj in str(path)
        assert len(nota.xml_hash) == 64  # SHA-256 hex


def test_consulta_dedupe_nao_duplica_nfse_repetida(db_session, cliente, storage):
    """Mesma NFS-e retornada duas vezes → 1 registro (segunda execução atualiza)."""
    notas = [_mk_nota("00000001")]
    payload = ConsultaCreate(
        cliente_id=cliente.id,
        tipo=TipoConsulta.periodo_emissao,
        parametros=ConsultaParametros(data_inicial=date(2026, 1, 1), data_final=date(2026, 1, 31)),
    )

    with _mock_giss_client(notas):
        r1 = ConsultaService(db_session, storage=storage).executar(payload)
        r2 = ConsultaService(db_session, storage=storage).executar(payload)

    assert r1.novos_xmls == 1
    assert r2.novos_xmls == 0  # segunda rodada: nada novo
    assert db_session.query(NfseXml).count() == 1


def test_consulta_atualiza_status_ao_cancelar(db_session, cliente, storage):
    """Primeira consulta: nota normal. Segunda: mesma nota marcada como cancelada."""
    payload = ConsultaCreate(
        cliente_id=cliente.id,
        tipo=TipoConsulta.periodo_emissao,
        parametros=ConsultaParametros(data_inicial=date(2026, 1, 1), data_final=date(2026, 1, 31)),
    )

    with _mock_giss_client([_mk_nota("00000001", status=1)]):
        ConsultaService(db_session, storage=storage).executar(payload)
    with _mock_giss_client([_mk_nota("00000001", status=2)]):
        ConsultaService(db_session, storage=storage).executar(payload)

    notas = db_session.query(NfseXml).all()
    assert len(notas) == 1
    assert notas[0].status_nfse == 2


def test_consulta_erro_giss_marca_status_erro(db_session, cliente, storage):
    payload = ConsultaCreate(
        cliente_id=cliente.id,
        tipo=TipoConsulta.periodo_emissao,
        parametros=ConsultaParametros(data_inicial=date(2026, 1, 1), data_final=date(2026, 1, 31)),
    )

    class FailingClient:
        def consultar_todas_paginas(self, *a, **kw):
            raise GISSException("[E142] Inscrição municipal inválida", codigo="E142")

        def close(self):
            pass

    @contextmanager
    def fake_builder(cliente):
        yield FailingClient()

    with patch("app.services.consulta.build_client_for_cliente", fake_builder):
        resumo = ConsultaService(db_session, storage=storage).executar(payload)

    assert resumo.status == StatusConsulta.erro
    assert "E142" in resumo.erro_mensagem
    assert resumo.total_notas == 0
    assert db_session.query(NfseXml).count() == 0


def test_consulta_cliente_inexistente_levanta(db_session, storage):
    payload = ConsultaCreate(
        cliente_id="00000000-0000-0000-0000-000000000000",
        tipo=TipoConsulta.periodo_emissao,
        parametros=ConsultaParametros(data_inicial=date(2026, 1, 1), data_final=date(2026, 1, 31)),
    )
    with pytest.raises(ValueError, match="não encontrado"):
        ConsultaService(db_session, storage=storage).executar(payload)


def test_consulta_cliente_inativo_levanta(db_session, cliente, storage):
    cliente.ativo = False
    db_session.commit()

    payload = ConsultaCreate(
        cliente_id=cliente.id,
        tipo=TipoConsulta.periodo_emissao,
        parametros=ConsultaParametros(data_inicial=date(2026, 1, 1), data_final=date(2026, 1, 31)),
    )
    with pytest.raises(ValueError, match="inativo"):
        ConsultaService(db_session, storage=storage).executar(payload)


def test_consulta_por_faixa_chama_metodo_correto(db_session, cliente, storage):
    """Garante que o tipo=faixa dispara a rota correta no GISSClient."""
    payload = ConsultaCreate(
        cliente_id=cliente.id,
        tipo=TipoConsulta.faixa,
        parametros=ConsultaParametros(nfse_inicial=1, nfse_final=100),
    )

    metodos_chamados = []

    class RecordingClient:
        def consultar_todas_paginas(self, metodo_nome, **kwargs):
            metodos_chamados.append((metodo_nome, kwargs))
            return [_mk_nota("00000050")]

        def close(self):
            pass

    @contextmanager
    def fake_builder(cliente):
        yield RecordingClient()

    with patch("app.services.consulta.build_client_for_cliente", fake_builder):
        resumo = ConsultaService(db_session, storage=storage).executar(payload)

    assert resumo.status == StatusConsulta.sucesso
    assert len(metodos_chamados) == 1
    assert metodos_chamados[0][0] == "faixa"
    assert metodos_chamados[0][1]["nfse_inicial"] == 1
    assert metodos_chamados[0][1]["nfse_final"] == 100


def test_consulta_registra_duracao_e_timestamps(db_session, cliente, storage):
    payload = ConsultaCreate(
        cliente_id=cliente.id,
        tipo=TipoConsulta.periodo_emissao,
        parametros=ConsultaParametros(data_inicial=date(2026, 1, 1), data_final=date(2026, 1, 31)),
    )

    with _mock_giss_client([_mk_nota("00000001")]):
        resumo = ConsultaService(db_session, storage=storage).executar(payload)

    from app.models import Consulta

    consulta = db_session.get(Consulta, resumo.consulta_id)
    assert consulta.iniciado_em is not None
    assert consulta.finalizado_em is not None
    assert consulta.duracao_ms is not None and consulta.duracao_ms >= 0
    assert consulta.total_notas == 1
