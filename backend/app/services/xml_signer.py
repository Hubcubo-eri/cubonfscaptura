"""Assinatura XML padrão GISS/ABRASF (xmldsig RSA-SHA1)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from lxml import etree

from app.giss.constants import ELEMENTOS_SIGNATURE_PROIBIDOS, NS_DSIG
from app.services.certificado import CertificadoService


class XMLSignerService:
    """Assina XMLs conforme exigência do GISS.

    Padrão:
    - Canonicalization: http://www.w3.org/TR/2001/REC-xml-c14n-20010315
    - Signature: http://www.w3.org/2000/09/xmldsig#rsa-sha1
    - Digest: http://www.w3.org/2000/09/xmldsig#sha1
    - Transform: enveloped-signature + c14n
    - KeyInfo: apenas X509Certificate (Base64)
    """

    def __init__(self, pfx_path: str | Path, pfx_password: str):
        self.private_key, self.certificate, self.ca_chain = CertificadoService.load_pfx(pfx_path, pfx_password)

    def sign(self, xml_bytes: bytes, reference_uri: Optional[str] = None) -> bytes:
        """Assina o XML retornando os bytes assinados.

        Args:
            xml_bytes: XML a ser assinado.
            reference_uri: URI opcional para a Reference (usado em LoteRps, InfPedidoCancelamento, etc.)
        """
        # Import local para não onerar o startup quando não usado
        from signxml import XMLSigner, methods

        root = etree.fromstring(xml_bytes)

        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha1",
            digest_algorithm="sha1",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
        )
        # GISS exige que KeyInfo contenha apenas X509Certificate
        signer.excise_empty_xmlns_declarations = True

        signed_root = signer.sign(
            root,
            key=self.private_key,
            cert=[self.certificate],
            reference_uri=reference_uri,
        )

        self._clean_signature(signed_root)

        return etree.tostring(signed_root, xml_declaration=True, encoding="UTF-8", standalone=None)

    @staticmethod
    def _clean_signature(root: etree._Element) -> None:
        """Remove elementos não permitidos pelo padrão GISS da <Signature>."""
        for tag in ELEMENTOS_SIGNATURE_PROIBIDOS:
            for el in root.findall(f".//ds:{tag}", NS_DSIG):
                parent = el.getparent()
                if parent is not None:
                    parent.remove(el)
