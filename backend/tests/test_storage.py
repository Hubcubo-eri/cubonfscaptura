"""Testes do StorageService."""
from __future__ import annotations

import zipfile
from datetime import date
from io import BytesIO

from app.services.storage import StorageService


def test_hash_xml_determinista():
    s = StorageService.hash_xml("<x/>")
    assert s == StorageService.hash_xml("<x/>")
    assert s != StorageService.hash_xml("<y/>")
    assert len(s) == 64  # SHA-256 hex


def test_save_xml_cria_estrutura_hierarquica(tmp_path):
    storage = StorageService(base_path=tmp_path)
    path, hash_ = storage.save_xml(
        cnpj="12345678000199",
        numero="00000001",
        competencia=date(2026, 1, 15),
        xml_content="<nfse><numero>1</numero></nfse>",
    )
    assert path.exists()
    assert path.parent.name == "2026-01"
    assert path.parent.parent.name == "12345678000199"
    assert path.name == "nfse_00000001.xml"
    assert len(hash_) == 64


def test_save_xml_sobrescreve_mesmo_numero(tmp_path):
    storage = StorageService(base_path=tmp_path)
    p1, h1 = storage.save_xml("123", "1", date(2026, 1, 1), "<a/>")
    p2, h2 = storage.save_xml("123", "1", date(2026, 1, 1), "<b/>")
    assert p1 == p2
    assert h1 != h2
    assert p2.read_text() == "<b/>"


def test_save_xml_sem_competencia_usa_fallback(tmp_path):
    storage = StorageService(base_path=tmp_path)
    path, _ = storage.save_xml("123", "99", None, "<x/>")
    assert path.parent.name == "sem-competencia"


def test_save_xml_numero_com_caracteres_especiais_sanitizado(tmp_path):
    storage = StorageService(base_path=tmp_path)
    path, _ = storage.save_xml("123", "AB/01-X", date(2026, 2, 1), "<x/>")
    assert "/" not in path.name
    assert "-" not in path.name
    assert path.name == "nfse_AB01X.xml"


def test_build_zip_inclui_arquivos(tmp_path):
    storage = StorageService(base_path=tmp_path)
    p1, _ = storage.save_xml("123", "1", date(2026, 1, 1), "<a/>")
    p2, _ = storage.save_xml("123", "2", date(2026, 1, 1), "<b/>")

    zip_bytes = storage.build_zip(
        [("cliente/01.xml", p1), ("cliente/02.xml", p2)]
    )

    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        names = set(zf.namelist())
        assert names == {"cliente/01.xml", "cliente/02.xml"}
        assert zf.read("cliente/01.xml") == b"<a/>"


def test_build_zip_ignora_arquivos_inexistentes(tmp_path):
    storage = StorageService(base_path=tmp_path)
    zip_bytes = storage.build_zip([("x.xml", tmp_path / "nao-existe.xml")])
    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        assert zf.namelist() == []
