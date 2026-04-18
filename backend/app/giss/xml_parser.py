"""Parse dos XMLs de response do GISS."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from lxml import etree

from app.giss import GISSException
from app.giss.constants import NS_ABRASF


@dataclass
class NfseData:
    """Dados extraídos de uma NFS-e retornada pelo GISS."""

    numero: str = ""
    codigo_verificacao: str = ""
    data_emissao: Optional[datetime] = None
    competencia: Optional[date] = None
    valor_servicos: Decimal = Decimal("0")
    valor_deducoes: Decimal = Decimal("0")
    valor_iss: Decimal = Decimal("0")
    valor_liquido: Decimal = Decimal("0")
    aliquota: Decimal = Decimal("0")
    base_calculo: Decimal = Decimal("0")
    cnpj_prestador: str = ""
    im_prestador: str = ""
    razao_social_prestador: str = ""
    cnpj_tomador: Optional[str] = None
    razao_social_tomador: Optional[str] = None
    item_lista_servico: str = ""
    discriminacao: str = ""
    codigo_municipio: str = ""
    status: int = 1  # 1=Normal, 2=Cancelada
    xml_completo: str = ""


@dataclass
class PaginaResultado:
    """Resultado de uma página de consulta GISS."""

    notas: List[NfseData] = field(default_factory=list)
    pagina: int = 1
    tem_mais_paginas: bool = False


def _decimal(parent: Optional[etree._Element], xpath: str) -> Decimal:
    if parent is None:
        return Decimal("0")
    val = parent.findtext(xpath, namespaces=NS_ABRASF, default="0")
    try:
        return Decimal(val.replace(",", ".") if val else "0")
    except Exception:
        return Decimal("0")


def _text(parent: Optional[etree._Element], xpath: str, default: str = "") -> str:
    if parent is None:
        return default
    return (parent.findtext(xpath, namespaces=NS_ABRASF, default=default) or default).strip()


def _get_doc(parent: Optional[etree._Element], base_xpath: str) -> str:
    """Busca CNPJ ou CPF dentro de CpfCnpj."""
    if parent is None:
        return ""
    cnpj = _text(parent, f"{base_xpath}//nfse:Cnpj")
    if cnpj:
        return cnpj
    return _text(parent, f"{base_xpath}//nfse:Cpf")


def _parse_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:19], fmt)
        except ValueError:
            continue
    return None


def _parse_date(value: str) -> Optional[date]:
    dt = _parse_datetime(value)
    return dt.date() if dt else None


def _check_erros(root: etree._Element) -> None:
    """Verifica mensagens de retorno com erro e lança GISSException."""
    erros = root.findall(".//nfse:ListaMensagemRetorno/nfse:MensagemRetorno", NS_ABRASF)
    if not erros:
        return

    mensagens = []
    codigos = []
    for erro in erros:
        codigo = _text(erro, "nfse:Codigo")
        mensagem = _text(erro, "nfse:Mensagem")
        correcao = _text(erro, "nfse:Correcao")
        texto = f"[{codigo}] {mensagem}"
        if correcao:
            texto += f" — {correcao}"
        mensagens.append(texto)
        codigos.append(codigo)

    raise GISSException("; ".join(mensagens), codigo="|".join(codigos))


def _parse_nota(comp: etree._Element) -> Optional[NfseData]:
    """Extrai NfseData de um elemento <CompNfse>."""
    inf = comp.find(".//nfse:InfNfse", NS_ABRASF)
    if inf is None:
        return None

    decl = inf.find(".//nfse:DeclaracaoPrestacaoServico//nfse:InfDeclaracaoPrestacaoServico", NS_ABRASF)
    if decl is None:
        # Alguns layouts trazem o Servico diretamente em InfNfse
        decl = inf

    servico = decl.find("nfse:Servico", NS_ABRASF) if decl is not None else None
    valores_nfse = inf.find("nfse:ValoresNfse", NS_ABRASF)
    valores_servico = servico.find("nfse:Valores", NS_ABRASF) if servico is not None else None

    prestador = inf.find(".//nfse:PrestadorServico", NS_ABRASF)
    tomador = decl.find(".//nfse:TomadorServico", NS_ABRASF) if decl is not None else None

    nota = NfseData(
        numero=_text(inf, "nfse:Numero"),
        codigo_verificacao=_text(inf, "nfse:CodigoVerificacao"),
        data_emissao=_parse_datetime(_text(inf, "nfse:DataEmissao")),
        competencia=_parse_date(_text(decl, "nfse:Competencia")) if decl is not None else None,
        valor_servicos=_decimal(valores_servico, "nfse:ValorServicos"),
        valor_deducoes=_decimal(valores_servico, "nfse:ValorDeducoes"),
        valor_iss=_decimal(valores_nfse, "nfse:ValorIss"),
        valor_liquido=_decimal(valores_nfse, "nfse:ValorLiquidoNfse"),
        aliquota=_decimal(valores_servico, "nfse:Aliquota"),
        base_calculo=_decimal(valores_nfse, "nfse:BaseCalculo"),
        cnpj_prestador=_get_doc(prestador, ".//nfse:IdentificacaoPrestador"),
        im_prestador=_text(prestador, ".//nfse:IdentificacaoPrestador//nfse:InscricaoMunicipal"),
        razao_social_prestador=_text(prestador, "nfse:RazaoSocial"),
        cnpj_tomador=_get_doc(tomador, ".//nfse:IdentificacaoTomador") or None,
        razao_social_tomador=_text(tomador, "nfse:RazaoSocial") or None,
        item_lista_servico=_text(servico, "nfse:ItemListaServico"),
        discriminacao=_text(servico, "nfse:Discriminacao"),
        codigo_municipio=_text(servico, "nfse:CodigoMunicipio"),
        status=2 if comp.find("nfse:NfseCancelamento", NS_ABRASF) is not None else 1,
        xml_completo=etree.tostring(comp, encoding="unicode"),
    )
    return nota


def parse_consulta_response(xml_response: str) -> PaginaResultado:
    """Parseia o retorno XML de uma consulta GISS.

    Funciona para ConsultarNfseServicoPrestadoResposta e ConsultarNfseFaixaResposta.
    Lança GISSException se houver <MensagemRetorno>.
    """
    if isinstance(xml_response, str):
        xml_bytes = xml_response.encode("utf-8")
    else:
        xml_bytes = xml_response

    root = etree.fromstring(xml_bytes)
    _check_erros(root)

    notas: List[NfseData] = []
    for comp in root.findall(".//nfse:CompNfse", NS_ABRASF):
        nota = _parse_nota(comp)
        if nota is not None:
            notas.append(nota)

    pagina_text = _text(root, ".//nfse:ListaNfse/nfse:Pagina") or "1"
    try:
        pagina_atual = int(pagina_text)
    except ValueError:
        pagina_atual = 1

    from app.giss.constants import GISS_MAX_NOTAS_POR_PAGINA

    return PaginaResultado(
        notas=notas,
        pagina=pagina_atual,
        tem_mais_paginas=len(notas) >= GISS_MAX_NOTAS_POR_PAGINA,
    )


def extract_comp_nfse_xml(xml_response: str) -> List[str]:
    """Retorna lista de XMLs <CompNfse> individuais, cada um como string autônoma."""
    if isinstance(xml_response, str):
        xml_bytes = xml_response.encode("utf-8")
    else:
        xml_bytes = xml_response

    root = etree.fromstring(xml_bytes)
    _check_erros(root)

    xmls = []
    for comp in root.findall(".//nfse:CompNfse", NS_ABRASF):
        xmls.append(etree.tostring(comp, xml_declaration=True, encoding="UTF-8", standalone=None).decode("utf-8"))
    return xmls
