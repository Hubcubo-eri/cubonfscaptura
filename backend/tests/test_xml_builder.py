"""Testes de geração dos XMLs de request GISS (padrão ABRASF 2.04)."""
from __future__ import annotations

from datetime import date

from lxml import etree

from app.giss import xml_builder
from app.giss.constants import GISS_NAMESPACE

NS = {"n": GISS_NAMESPACE}


def _parse(xml_bytes: bytes) -> etree._Element:
    return etree.fromstring(xml_bytes)


def test_cabecalho_tem_versao_e_versao_dados():
    xml = xml_builder.build_cabecalho()
    root = _parse(xml)
    assert root.tag == f"{{{GISS_NAMESPACE}}}cabecalho"
    assert root.get("versao") == "2.04"
    versao_dados = root.find("n:versaoDados", NS)
    assert versao_dados is not None and versao_dados.text == "2.04"


def test_consulta_servico_prestado_estrutura_periodo_emissao():
    xml = xml_builder.build_consulta_servico_prestado(
        cnpj="12345678000199",
        inscricao_municipal="998877",
        data_inicial=date(2026, 1, 1),
        data_final=date(2026, 1, 31),
        pagina=1,
        tipo_periodo="emissao",
    )
    root = _parse(xml)
    assert root.tag == f"{{{GISS_NAMESPACE}}}ConsultarNfseServicoPrestadoEnvio"
    assert root.find(".//n:Prestador/n:CpfCnpj/n:Cnpj", NS).text == "12345678000199"
    assert root.find(".//n:Prestador/n:InscricaoMunicipal", NS).text == "998877"
    assert root.find(".//n:PeriodoEmissao/n:DataInicial", NS).text == "2026-01-01"
    assert root.find(".//n:PeriodoEmissao/n:DataFinal", NS).text == "2026-01-31"
    # Sem PeriodoCompetencia
    assert root.find(".//n:PeriodoCompetencia", NS) is None
    assert root.find(".//n:Pagina", NS).text == "1"


def test_consulta_servico_prestado_periodo_competencia():
    xml = xml_builder.build_consulta_servico_prestado(
        cnpj="12345678000199",
        inscricao_municipal="998877",
        data_inicial=date(2026, 2, 1),
        data_final=date(2026, 2, 28),
        tipo_periodo="competencia",
    )
    root = _parse(xml)
    assert root.find(".//n:PeriodoCompetencia/n:DataInicial", NS).text == "2026-02-01"
    assert root.find(".//n:PeriodoEmissao", NS) is None


def test_consulta_faixa_estrutura():
    xml = xml_builder.build_consulta_faixa(
        cnpj="12345678000199",
        inscricao_municipal="998877",
        nfse_inicial=1000,
        nfse_final=1050,
        pagina=2,
    )
    root = _parse(xml)
    assert root.tag == f"{{{GISS_NAMESPACE}}}ConsultarNfseFaixaEnvio"
    assert root.find(".//n:Faixa/n:NumeroNfseInicial", NS).text == "1000"
    assert root.find(".//n:Faixa/n:NumeroNfseFinal", NS).text == "1050"
    assert root.find(".//n:Pagina", NS).text == "2"


def test_consulta_por_rps_estrutura():
    xml = xml_builder.build_consulta_por_rps(
        cnpj="12345678000199",
        inscricao_municipal="998877",
        numero_rps=42,
        serie_rps="A",
        tipo_rps=1,
    )
    root = _parse(xml)
    assert root.tag == f"{{{GISS_NAMESPACE}}}ConsultarNfseRpsEnvio"
    identificacao = root.find("n:IdentificacaoRps", NS)
    assert identificacao is not None
    assert identificacao.find("n:Numero", NS).text == "42"
    assert identificacao.find("n:Serie", NS).text == "A"
    assert identificacao.find("n:Tipo", NS).text == "1"


def test_xml_tem_declaracao_utf8():
    xml = xml_builder.build_cabecalho()
    assert xml.startswith(b"<?xml")
    assert b"UTF-8" in xml[:60] or b"utf-8" in xml[:60]
