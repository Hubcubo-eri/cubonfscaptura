"""Serviço de manipulação de certificados A1 (.pfx)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID


@dataclass
class CertificadoInfo:
    cn: Optional[str]
    cnpj: Optional[str]
    validade_inicio: Optional[date]
    validade_fim: Optional[date]
    hash_sha256: str

    @property
    def vencido(self) -> bool:
        return bool(self.validade_fim and self.validade_fim < date.today())

    @property
    def dias_para_vencer(self) -> Optional[int]:
        if not self.validade_fim:
            return None
        return (self.validade_fim - date.today()).days


class CertificadoService:
    """Lê, valida e extrai metadados de certificados .pfx."""

    @staticmethod
    def load_pfx(pfx_path: str | Path, password: str) -> Tuple[object, object, list]:
        """Carrega chave privada, certificado e cadeia CA a partir de um .pfx."""
        data = Path(pfx_path).read_bytes()
        private_key, certificate, ca_chain = pkcs12.load_key_and_certificates(
            data, password.encode("utf-8"), default_backend()
        )
        if private_key is None or certificate is None:
            raise ValueError("Certificado .pfx inválido ou senha incorreta")
        return private_key, certificate, ca_chain or []

    @staticmethod
    def extract_info(pfx_bytes: bytes, password: str) -> CertificadoInfo:
        """Extrai metadados do .pfx em memória (sem gravar no disco)."""
        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            pfx_bytes, password.encode("utf-8"), default_backend()
        )
        if certificate is None:
            raise ValueError("Certificado .pfx inválido ou senha incorreta")

        cn = None
        cnpj = None
        try:
            cn_attrs = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
            if cn_attrs:
                cn = cn_attrs[0].value
                # CN do e-CNPJ geralmente contém "NOME:CNPJ"
                if ":" in cn:
                    possible_cnpj = "".join(c for c in cn.split(":")[-1] if c.isdigit())
                    if len(possible_cnpj) == 14:
                        cnpj = possible_cnpj
        except Exception:
            pass

        # Usa validade em UTC
        try:
            validade_inicio = certificate.not_valid_before_utc.date()
            validade_fim = certificate.not_valid_after_utc.date()
        except AttributeError:  # cryptography < 42 fallback
            validade_inicio = certificate.not_valid_before.replace(tzinfo=timezone.utc).date()
            validade_fim = certificate.not_valid_after.replace(tzinfo=timezone.utc).date()

        return CertificadoInfo(
            cn=cn,
            cnpj=cnpj,
            validade_inicio=validade_inicio,
            validade_fim=validade_fim,
            hash_sha256=hashlib.sha256(pfx_bytes).hexdigest(),
        )

    @staticmethod
    def save_pfx(pfx_bytes: bytes, dest_path: str | Path) -> Path:
        """Grava os bytes do .pfx no filesystem."""
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(pfx_bytes)
        # Permissão restritiva (best-effort; pode falhar no Windows)
        try:
            dest.chmod(0o600)
        except Exception:
            pass
        return dest
