"""Serviço de armazenamento de XMLs no filesystem."""
from __future__ import annotations

import hashlib
import io
import zipfile
from datetime import date
from pathlib import Path
from typing import Iterable, Optional, Tuple

from app.config import get_settings


class StorageService:
    """Gerencia a gravação organizada de XMLs por cliente/competência."""

    def __init__(self, base_path: Optional[str | Path] = None):
        settings = get_settings()
        self.base_path = Path(base_path or settings.xml_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def hash_xml(xml_content: str | bytes) -> str:
        """Gera SHA-256 do XML para deduplicação."""
        if isinstance(xml_content, str):
            xml_content = xml_content.encode("utf-8")
        return hashlib.sha256(xml_content).hexdigest()

    def _resolve_path(self, cnpj: str, competencia: Optional[date], numero: str) -> Path:
        """Resolve o path final: {base}/{cnpj}/{YYYY-MM}/nfse_{numero}.xml"""
        periodo = competencia.strftime("%Y-%m") if competencia else "sem-competencia"
        safe_numero = "".join(c for c in numero if c.isalnum()) or "sem-numero"
        return self.base_path / cnpj / periodo / f"nfse_{safe_numero}.xml"

    def save_xml(
        self,
        cnpj: str,
        numero: str,
        competencia: Optional[date],
        xml_content: str,
    ) -> Tuple[Path, str]:
        """Salva XML no filesystem. Retorna (path, hash_sha256)."""
        path = self._resolve_path(cnpj, competencia, numero)
        path.parent.mkdir(parents=True, exist_ok=True)

        xml_bytes = xml_content.encode("utf-8") if isinstance(xml_content, str) else xml_content
        path.write_bytes(xml_bytes)
        return path, self.hash_xml(xml_bytes)

    def read_xml(self, path: str | Path) -> bytes:
        return Path(path).read_bytes()

    def build_zip(self, xmls: Iterable[Tuple[str, str | Path]]) -> bytes:
        """Monta um ZIP em memória a partir de pares (nome_arquivo, path)."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for arcname, path in xmls:
                p = Path(path)
                if p.exists():
                    zf.write(p, arcname=arcname)
        buffer.seek(0)
        return buffer.getvalue()
