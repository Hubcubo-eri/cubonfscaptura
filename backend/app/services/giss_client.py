"""Cliente SOAP para o Web Service GISS Online.

Responsabilidades:
- Estabelecer conexão mTLS (TLS 1.2 obrigatório) com o Web Service usando o
  certificado A1 (.pfx) do prestador.
- Montar o cabeçalho ABRASF, delegar a construção do XML de dados para o
  ``xml_builder`` e a assinatura para o ``XMLSignerService``.
- Invocar os métodos SOAP síncronos (ConsultarNfseServicoPrestado,
  ConsultarNfsePorFaixa, ConsultarNfsePorRps) e capturar o XML cru da resposta
  via history plugin do zeep.
- Iterar automaticamente pelas páginas de 50 notas/página.
- Traduzir SOAPFault e exceções de transporte em ``GISSException``.
"""
from __future__ import annotations

import logging
import ssl
import tempfile
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any, Callable, Iterator, List, Optional, Tuple

from cryptography.hazmat.primitives import serialization

from app.config import get_settings
from app.giss import GISSException
from app.giss import xml_builder
from app.giss.constants import GISS_MAX_NOTAS_POR_PAGINA, METODOS
from app.giss.xml_parser import NfseData, PaginaResultado, parse_consulta_response
from app.services.certificado import CertificadoService
from app.services.xml_signer import XMLSignerService

logger = logging.getLogger(__name__)


# ======================================================================== TLS
class _TLS12HTTPAdapter:
    """Lazy factory de HTTPAdapter que força TLS 1.2+.

    Implementado como classe para permitir import tardio de requests/urllib3
    (evita custo se o módulo for importado sem disparar consulta).
    """

    @staticmethod
    def build():
        from requests.adapters import HTTPAdapter
        from urllib3.poolmanager import PoolManager
        from urllib3.util.ssl_ import create_urllib3_context

        class TLS12Adapter(HTTPAdapter):
            def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
                ctx = create_urllib3_context()
                # GISS exige TLS 1.2 mínimo. Alguns servidores não respondem
                # bem se o cliente ofertar TLS 1.3 — travar em 1.2 é o caminho
                # mais seguro.
                ctx.minimum_version = ssl.TLSVersion.TLSv1_2
                ctx.maximum_version = ssl.TLSVersion.TLSv1_2
                kwargs["ssl_context"] = ctx
                self.poolmanager = PoolManager(
                    num_pools=connections,
                    maxsize=maxsize,
                    block=block,
                    **kwargs,
                )

        return TLS12Adapter()


# ===================================================================== Client
class GISSClient:
    """Cliente SOAP GISS com autenticação mTLS via certificado A1.

    Uso típico::

        with GISSClient(pfx_path, pfx_password) as client:
            resultado = client.consultar_servico_prestado(
                cnpj, im, data_inicial, data_final,
            )
    """

    def __init__(
        self,
        pfx_path: str | Path,
        pfx_password: str,
        wsdl_url: Optional[str] = None,
        timeout: Optional[int] = None,
        verify_ssl: bool = True,
    ):
        settings = get_settings()
        self.pfx_path = Path(pfx_path)
        self.pfx_password = pfx_password
        self.wsdl_url = wsdl_url or settings.giss_wsdl_maceio
        self.timeout = timeout or settings.giss_timeout_seconds
        self.verify_ssl = verify_ssl

        # O XMLSigner é pesado (carrega a chave privada); construir uma vez.
        self.xml_signer = XMLSignerService(self.pfx_path, self.pfx_password)

        self._tmpdir: Optional[tempfile.TemporaryDirectory] = None
        self._cert_pem_path: Optional[Path] = None
        self._key_pem_path: Optional[Path] = None
        self._zeep_client: Optional[Any] = None
        self._history_plugin: Optional[Any] = None

    # ----------------------------------------------------------- context mgr
    def __enter__(self) -> "GISSClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        """Libera arquivos PEM temporários."""
        if self._tmpdir is not None:
            try:
                self._tmpdir.cleanup()
            except Exception:
                logger.debug("Falha ao limpar tmpdir de cert", exc_info=True)
            self._tmpdir = None
            self._cert_pem_path = None
            self._key_pem_path = None

    # ----------------------------------------------------------------- TLS
    def _ensure_pem_files(self) -> None:
        """Extrai cert/key do .pfx para PEM temporários (requests exige arquivos)."""
        if self._cert_pem_path and self._key_pem_path:
            return

        private_key, certificate, _ = CertificadoService.load_pfx(self.pfx_path, self.pfx_password)
        self._tmpdir = tempfile.TemporaryDirectory(prefix="giss-ssl-")
        tmp = Path(self._tmpdir.name)

        cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        self._cert_pem_path = tmp / "cert.pem"
        self._key_pem_path = tmp / "key.pem"
        self._cert_pem_path.write_bytes(cert_pem)
        self._key_pem_path.write_bytes(key_pem)
        for p in (self._cert_pem_path, self._key_pem_path):
            try:
                p.chmod(0o600)
            except Exception:
                pass

    # --------------------------------------------------------- zeep client
    def _build_client(self):
        """Constrói o cliente zeep com sessão TLS 1.2 + mTLS + history plugin."""
        from requests import Session
        from zeep import Client
        from zeep.plugins import HistoryPlugin
        from zeep.transports import Transport

        self._ensure_pem_files()

        session = Session()
        session.cert = (str(self._cert_pem_path), str(self._key_pem_path))
        session.verify = self.verify_ssl
        session.mount("https://", _TLS12HTTPAdapter.build())

        transport = Transport(session=session, timeout=self.timeout, operation_timeout=self.timeout)
        self._history_plugin = HistoryPlugin(maxlen=5)
        return Client(wsdl=self.wsdl_url, transport=transport, plugins=[self._history_plugin])

    @property
    def zeep_client(self):
        if self._zeep_client is None:
            logger.info("Construindo cliente SOAP GISS: %s", self.wsdl_url)
            self._zeep_client = self._build_client()
        return self._zeep_client

    # --------------------------------------------------------- SOAP invoke
    def _last_envelopes(self) -> Tuple[Optional[str], Optional[str]]:
        """Retorna (envelope_enviado, envelope_recebido) da última chamada."""
        from lxml import etree

        if self._history_plugin is None:
            return None, None

        try:
            sent = self._history_plugin.last_sent
            recv = self._history_plugin.last_received
            sent_xml = etree.tostring(sent["envelope"], pretty_print=True).decode() if sent else None
            recv_xml = etree.tostring(recv["envelope"], pretty_print=True).decode() if recv else None
            return sent_xml, recv_xml
        except Exception:
            return None, None

    def _call_soap(self, metodo: str, cabecalho: bytes, xml_assinado: bytes) -> str:
        """Invoca um método SOAP do GISS e retorna a string XML de resposta."""
        from requests.exceptions import ConnectionError as ReqConnError
        from requests.exceptions import SSLError, Timeout
        from zeep.exceptions import Fault, TransportError, XMLParseError

        try:
            service = getattr(self.zeep_client.service, metodo)
        except AttributeError as e:
            raise GISSException(f"Método SOAP desconhecido: {metodo}") from e

        try:
            response = service(cabecalho.decode("utf-8"), xml_assinado.decode("utf-8"))
        except Fault as e:
            raise GISSException(f"SOAPFault: {e.message}", codigo=getattr(e, "code", None)) from e
        except TransportError as e:
            raise GISSException(f"Erro de transporte GISS (HTTP {e.status_code})") from e
        except XMLParseError as e:
            raise GISSException(f"Resposta GISS com XML inválido: {e}") from e
        except SSLError as e:
            raise GISSException(f"Falha TLS com o GISS: {e}") from e
        except Timeout as e:
            raise GISSException(f"Timeout ao chamar GISS após {self.timeout}s") from e
        except ReqConnError as e:
            raise GISSException(f"Falha de conexão com GISS: {e}") from e

        if isinstance(response, bytes):
            return response.decode("utf-8")
        return str(response)

    # ----------------------------------------------------------- métodos WS
    def consultar_servico_prestado(
        self,
        cnpj: str,
        inscricao_municipal: str,
        data_inicial: date,
        data_final: date,
        pagina: int = 1,
        tipo_periodo: str = "emissao",
    ) -> PaginaResultado:
        """ConsultarNfseServicoPrestado — consulta por período (síncrona)."""
        cabecalho = xml_builder.build_cabecalho()
        dados = xml_builder.build_consulta_servico_prestado(
            cnpj, inscricao_municipal, data_inicial, data_final, pagina, tipo_periodo
        )
        dados_assinado = self.xml_signer.sign(dados)
        logger.info(
            "GISS consultar_servico_prestado cnpj=%s im=%s periodo=%s..%s pag=%s",
            cnpj, inscricao_municipal, data_inicial, data_final, pagina,
        )
        response_xml = self._call_soap(
            METODOS["consultar_servico_prestado"], cabecalho, dados_assinado
        )
        return parse_consulta_response(response_xml)

    def consultar_por_faixa(
        self,
        cnpj: str,
        inscricao_municipal: str,
        nfse_inicial: int,
        nfse_final: int,
        pagina: int = 1,
    ) -> PaginaResultado:
        """ConsultarNfsePorFaixa — consulta por faixa de número (síncrona)."""
        cabecalho = xml_builder.build_cabecalho()
        dados = xml_builder.build_consulta_faixa(
            cnpj, inscricao_municipal, nfse_inicial, nfse_final, pagina
        )
        dados_assinado = self.xml_signer.sign(dados)
        logger.info(
            "GISS consultar_por_faixa cnpj=%s im=%s faixa=%s..%s pag=%s",
            cnpj, inscricao_municipal, nfse_inicial, nfse_final, pagina,
        )
        response_xml = self._call_soap(METODOS["consultar_faixa"], cabecalho, dados_assinado)
        return parse_consulta_response(response_xml)

    def consultar_por_rps(
        self,
        cnpj: str,
        inscricao_municipal: str,
        numero_rps: int,
        serie_rps: str,
        tipo_rps: int = 1,
    ) -> PaginaResultado:
        """ConsultarNfsePorRps — consulta NFS-e vinculada a um RPS específico."""
        cabecalho = xml_builder.build_cabecalho()
        dados = xml_builder.build_consulta_por_rps(
            cnpj, inscricao_municipal, numero_rps, serie_rps, tipo_rps
        )
        dados_assinado = self.xml_signer.sign(dados)
        logger.info(
            "GISS consultar_por_rps cnpj=%s im=%s rps=%s serie=%s tipo=%s",
            cnpj, inscricao_municipal, numero_rps, serie_rps, tipo_rps,
        )
        response_xml = self._call_soap(METODOS["consultar_rps"], cabecalho, dados_assinado)
        return parse_consulta_response(response_xml)

    # ----------------------------------------------------------- paginação
    def iterar_paginas(
        self,
        metodo: Callable[..., PaginaResultado],
        **kwargs: Any,
    ) -> Iterator[List[NfseData]]:
        """Itera automaticamente por todas as páginas até esgotar os resultados.

        A paginação do GISS retorna no máximo 50 notas/página. Quando a página
        vier com menos de 50 registros (ou vazia), consideramos como última.
        """
        pagina = 1
        while True:
            resultado = metodo(pagina=pagina, **kwargs)
            if resultado.notas:
                yield resultado.notas
            # Encerra se a página veio menor que o limite do GISS — é a última.
            if not resultado.tem_mais_paginas or len(resultado.notas) < GISS_MAX_NOTAS_POR_PAGINA:
                break
            pagina += 1

    def consultar_todas_paginas(self, metodo_nome: str, **kwargs: Any) -> List[NfseData]:
        """Consolida todas as páginas em uma única lista de ``NfseData``."""
        metodo_map: dict[str, Callable[..., PaginaResultado]] = {
            "servico_prestado": self.consultar_servico_prestado,
            "faixa": self.consultar_por_faixa,
            "rps": self.consultar_por_rps,
        }
        metodo = metodo_map.get(metodo_nome)
        if metodo is None:
            raise GISSException(f"Método desconhecido: {metodo_nome}")

        todas: List[NfseData] = []
        for lote in self.iterar_paginas(metodo, **kwargs):
            todas.extend(lote)
        logger.info("GISS %s: %d notas em %d chamadas", metodo_nome, len(todas), len(todas) // GISS_MAX_NOTAS_POR_PAGINA + 1)
        return todas


# ================================================================= helpers
@contextmanager
def build_client_for_cliente(cliente) -> Iterator[GISSClient]:
    """Context manager que constrói um ``GISSClient`` a partir do model ``Cliente``.

    Decifra a senha criptografada do certificado apenas dentro do escopo do
    ``with`` e garante o cleanup dos PEMs temporários ao sair.
    """
    from app.services.crypto import decrypt_secret

    if not cliente.cert_path or not cliente.cert_senha_enc:
        raise GISSException(f"Cliente {cliente.cnpj} não possui certificado configurado")

    senha = decrypt_secret(cliente.cert_senha_enc)
    client = GISSClient(cliente.cert_path, senha)
    try:
        yield client
    finally:
        client.close()
