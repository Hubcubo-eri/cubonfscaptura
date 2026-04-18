"""Construção dos XMLs de request para o GISS (padrão ABRASF)."""
from __future__ import annotations

from datetime import date
from typing import Optional

from lxml import etree

from app.giss.constants import GISS_CABECALHO_VERSAO, GISS_NAMESPACE

NSMAP = {None: GISS_NAMESPACE}


def _to_string(element: etree._Element) -> bytes:
    return etree.tostring(element, xml_declaration=True, encoding="UTF-8", standalone=None)


def build_cabecalho(versao: str = GISS_CABECALHO_VERSAO) -> bytes:
    """Monta o XML do cabeçalho padrão GISS/ABRASF.

    <cabecalho versao="2.04" xmlns="http://www.abrasf.org.br/nfse.xsd">
        <versaoDados>2.04</versaoDados>
    </cabecalho>
    """
    root = etree.Element("cabecalho", versao=versao, nsmap=NSMAP)
    versao_dados = etree.SubElement(root, "versaoDados")
    versao_dados.text = versao
    return _to_string(root)


def _append_prestador(parent: etree._Element, cnpj: str, inscricao_municipal: str) -> None:
    prestador = etree.SubElement(parent, "Prestador")
    cpfcnpj = etree.SubElement(prestador, "CpfCnpj")
    cnpj_el = etree.SubElement(cpfcnpj, "Cnpj")
    cnpj_el.text = cnpj
    im = etree.SubElement(prestador, "InscricaoMunicipal")
    im.text = inscricao_municipal


def build_consulta_servico_prestado(
    cnpj: str,
    inscricao_municipal: str,
    data_inicial: date,
    data_final: date,
    pagina: int = 1,
    tipo_periodo: str = "emissao",
) -> bytes:
    """Monta XML ConsultarNfseServicoPrestadoEnvio.

    Args:
        cnpj: CNPJ do prestador (14 dígitos).
        inscricao_municipal: IM do prestador.
        data_inicial/data_final: Datas do período.
        pagina: Número da página (para paginação).
        tipo_periodo: "emissao" (PeriodoEmissao) ou "competencia" (PeriodoCompetencia).
    """
    root = etree.Element("ConsultarNfseServicoPrestadoEnvio", nsmap=NSMAP)
    _append_prestador(root, cnpj, inscricao_municipal)

    tag_periodo = "PeriodoEmissao" if tipo_periodo == "emissao" else "PeriodoCompetencia"
    periodo = etree.SubElement(root, tag_periodo)
    etree.SubElement(periodo, "DataInicial").text = data_inicial.isoformat()
    etree.SubElement(periodo, "DataFinal").text = data_final.isoformat()

    etree.SubElement(root, "Pagina").text = str(pagina)
    return _to_string(root)


def build_consulta_faixa(
    cnpj: str,
    inscricao_municipal: str,
    nfse_inicial: int,
    nfse_final: int,
    pagina: int = 1,
) -> bytes:
    """Monta XML ConsultarNfseFaixaEnvio."""
    root = etree.Element("ConsultarNfseFaixaEnvio", nsmap=NSMAP)
    _append_prestador(root, cnpj, inscricao_municipal)

    faixa = etree.SubElement(root, "Faixa")
    etree.SubElement(faixa, "NumeroNfseInicial").text = str(nfse_inicial)
    etree.SubElement(faixa, "NumeroNfseFinal").text = str(nfse_final)

    etree.SubElement(root, "Pagina").text = str(pagina)
    return _to_string(root)


def build_consulta_por_rps(
    cnpj: str,
    inscricao_municipal: str,
    numero_rps: int,
    serie_rps: str,
    tipo_rps: int = 1,
) -> bytes:
    """Monta XML ConsultarNfseRpsEnvio."""
    root = etree.Element("ConsultarNfseRpsEnvio", nsmap=NSMAP)

    identificacao = etree.SubElement(root, "IdentificacaoRps")
    etree.SubElement(identificacao, "Numero").text = str(numero_rps)
    etree.SubElement(identificacao, "Serie").text = serie_rps
    etree.SubElement(identificacao, "Tipo").text = str(tipo_rps)

    _append_prestador(root, cnpj, inscricao_municipal)
    return _to_string(root)


def build_cancelar_nfse(
    cnpj: str,
    inscricao_municipal: str,
    numero_nfse: str,
    codigo_municipio: str,
    codigo_cancelamento: str = "1",
) -> bytes:
    """Monta XML CancelarNfseEnvio (para referência; não usado no MVP)."""
    root = etree.Element("CancelarNfseEnvio", nsmap=NSMAP)
    pedido = etree.SubElement(root, "Pedido")
    inf_pedido = etree.SubElement(pedido, "InfPedidoCancelamento", Id=f"CANC_{numero_nfse}")

    identificacao = etree.SubElement(inf_pedido, "IdentificacaoNfse")
    etree.SubElement(identificacao, "Numero").text = numero_nfse
    cpfcnpj = etree.SubElement(identificacao, "CpfCnpj")
    etree.SubElement(cpfcnpj, "Cnpj").text = cnpj
    etree.SubElement(identificacao, "InscricaoMunicipal").text = inscricao_municipal
    etree.SubElement(identificacao, "CodigoMunicipio").text = codigo_municipio

    etree.SubElement(inf_pedido, "CodigoCancelamento").text = codigo_cancelamento
    return _to_string(root)
