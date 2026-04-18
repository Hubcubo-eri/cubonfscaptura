"""Testes do parser de responses GISS."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.giss import GISSException
from app.giss.xml_parser import extract_comp_nfse_xml, parse_consulta_response


def _resposta_com_uma_nfse() -> str:
    """Amostra mínima compatível com ConsultarNfseServicoPrestadoResposta."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<ConsultarNfseServicoPrestadoResposta xmlns="http://www.abrasf.org.br/nfse.xsd">
  <ListaNfse>
    <CompNfse>
      <Nfse>
        <InfNfse>
          <Numero>00000001</Numero>
          <CodigoVerificacao>ABC123XYZ</CodigoVerificacao>
          <DataEmissao>2026-01-15T10:20:30</DataEmissao>
          <ValoresNfse>
            <BaseCalculo>1000.00</BaseCalculo>
            <ValorIss>50.00</ValorIss>
            <ValorLiquidoNfse>950.00</ValorLiquidoNfse>
          </ValoresNfse>
          <PrestadorServico>
            <IdentificacaoPrestador>
              <CpfCnpj><Cnpj>12345678000199</Cnpj></CpfCnpj>
              <InscricaoMunicipal>998877</InscricaoMunicipal>
            </IdentificacaoPrestador>
            <RazaoSocial>Cubo Teste LTDA</RazaoSocial>
          </PrestadorServico>
          <DeclaracaoPrestacaoServico>
            <InfDeclaracaoPrestacaoServico>
              <Competencia>2026-01-01</Competencia>
              <Servico>
                <Valores>
                  <ValorServicos>1000.00</ValorServicos>
                  <ValorDeducoes>0.00</ValorDeducoes>
                  <Aliquota>5.0</Aliquota>
                </Valores>
                <ItemListaServico>04.08</ItemListaServico>
                <Discriminacao>Serviços de saúde</Discriminacao>
                <CodigoMunicipio>2704302</CodigoMunicipio>
              </Servico>
              <TomadorServico>
                <IdentificacaoTomador>
                  <CpfCnpj><Cnpj>98765432000111</Cnpj></CpfCnpj>
                </IdentificacaoTomador>
                <RazaoSocial>Cliente Exemplo SA</RazaoSocial>
              </TomadorServico>
            </InfDeclaracaoPrestacaoServico>
          </DeclaracaoPrestacaoServico>
        </InfNfse>
      </Nfse>
    </CompNfse>
    <Pagina>1</Pagina>
  </ListaNfse>
</ConsultarNfseServicoPrestadoResposta>
"""


def _resposta_com_erro() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<ConsultarNfseServicoPrestadoResposta xmlns="http://www.abrasf.org.br/nfse.xsd">
  <ListaMensagemRetorno>
    <MensagemRetorno>
      <Codigo>E142</Codigo>
      <Mensagem>Inscrição municipal do prestador inválida</Mensagem>
      <Correcao>Verifique a IM cadastrada no GISS</Correcao>
    </MensagemRetorno>
  </ListaMensagemRetorno>
</ConsultarNfseServicoPrestadoResposta>
"""


def _resposta_com_cancelada() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<ConsultarNfseServicoPrestadoResposta xmlns="http://www.abrasf.org.br/nfse.xsd">
  <ListaNfse>
    <CompNfse>
      <Nfse>
        <InfNfse>
          <Numero>99</Numero>
          <DataEmissao>2026-03-10</DataEmissao>
          <ValoresNfse><ValorIss>0</ValorIss><ValorLiquidoNfse>0</ValorLiquidoNfse></ValoresNfse>
        </InfNfse>
      </Nfse>
      <NfseCancelamento>
        <Confirmacao>
          <Pedido><InfPedidoCancelamento/></Pedido>
          <DataHoraCancelamento>2026-03-11T12:00:00</DataHoraCancelamento>
        </Confirmacao>
      </NfseCancelamento>
    </CompNfse>
  </ListaNfse>
</ConsultarNfseServicoPrestadoResposta>
"""


def test_parse_uma_nfse_extrai_campos_principais():
    resultado = parse_consulta_response(_resposta_com_uma_nfse())
    assert len(resultado.notas) == 1
    nota = resultado.notas[0]
    assert nota.numero == "00000001"
    assert nota.codigo_verificacao == "ABC123XYZ"
    assert nota.valor_servicos == Decimal("1000.00")
    assert nota.valor_iss == Decimal("50.00")
    assert nota.valor_liquido == Decimal("950.00")
    assert nota.aliquota == Decimal("5.0")
    assert nota.cnpj_prestador == "12345678000199"
    assert nota.im_prestador == "998877"
    assert nota.cnpj_tomador == "98765432000111"
    assert nota.razao_social_tomador == "Cliente Exemplo SA"
    assert nota.item_lista_servico == "04.08"
    assert nota.codigo_municipio == "2704302"
    assert nota.status == 1
    assert nota.data_emissao is not None
    assert nota.competencia is not None
    assert nota.competencia.isoformat() == "2026-01-01"
    assert "<CompNfse" in nota.xml_completo


def test_parse_mensagem_retorno_levanta_giss_exception():
    with pytest.raises(GISSException) as exc:
        parse_consulta_response(_resposta_com_erro())
    assert "E142" in str(exc.value)
    assert exc.value.codigo == "E142"


def test_parse_detecta_nfse_cancelada():
    resultado = parse_consulta_response(_resposta_com_cancelada())
    assert len(resultado.notas) == 1
    assert resultado.notas[0].status == 2


def test_parse_pagina_unica_nao_tem_mais():
    """1 nota < 50 → tem_mais_paginas = False."""
    resultado = parse_consulta_response(_resposta_com_uma_nfse())
    assert resultado.tem_mais_paginas is False
    assert resultado.pagina == 1


def test_extract_comp_nfse_xml_retorna_xmls_individuais():
    xmls = extract_comp_nfse_xml(_resposta_com_uma_nfse())
    assert len(xmls) == 1
    assert "<CompNfse" in xmls[0]
    assert xmls[0].startswith("<?xml")


def test_extract_comp_nfse_xml_propaga_erro():
    with pytest.raises(GISSException):
        extract_comp_nfse_xml(_resposta_com_erro())
