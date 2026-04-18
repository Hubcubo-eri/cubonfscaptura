"""Constantes do Web Service GISS Maceió (padrão ABRASF 2.04)."""

GISS_WSDL_MACEIO = "https://ws-maceio.giss.com.br/service-ws/nf/nfse-ws?wsdl"
GISS_NAMESPACE = "http://www.abrasf.org.br/nfse.xsd"
GISS_CABECALHO_VERSAO = "2.04"

# Limites do GISS
GISS_MAX_NOTAS_POR_PAGINA = 50
GISS_MAX_RPS_POR_LOTE = 50

# Código do município de Maceió/AL (IBGE)
CODIGO_MUNICIPIO_MACEIO = "2704302"

# Métodos SOAP do GISS
METODOS = {
    "cancelar": "CancelarNfse",
    "recepcionar_lote": "RecepcionarLoteRps",
    "consultar_lote": "ConsultarLoteRps",
    "consultar_faixa": "ConsultarNfsePorFaixa",
    "consultar_rps": "ConsultarNfsePorRps",
    "consultar_servico_prestado": "ConsultarNfseServicoPrestado",
}

# Namespaces (para lxml XPath)
NS_ABRASF = {"nfse": GISS_NAMESPACE}
NS_DSIG = {"ds": "http://www.w3.org/2000/09/xmldsig#"}

# Elementos que o GISS NÃO aceita na Signature
ELEMENTOS_SIGNATURE_PROIBIDOS = [
    "X509SubjectName",
    "X509IssuerSerial",
    "X509IssuerName",
    "X509SerialNumber",
    "X509SKI",
    "KeyValue",
    "RSAKeyValue",
    "Modulus",
    "Exponent",
]
