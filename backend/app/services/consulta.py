"""Orquestração do fluxo de consulta: GISS → parse → persistência."""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.giss import GISSException
from app.giss.constants import GISS_MAX_NOTAS_POR_PAGINA
from app.giss.xml_parser import NfseData
from app.models import Cliente, Consulta, NfseXml, StatusConsulta, TipoConsulta
from app.schemas.consulta import ConsultaCreate, ConsultaResumo
from app.services.giss_client import build_client_for_cliente
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


class ConsultaService:
    """Orquestra consultas ao GISS e persiste os XMLs capturados."""

    def __init__(self, db: Session, storage: Optional[StorageService] = None):
        self.db = db
        self.storage = storage or StorageService()

    # ------------------------------------------------------------------ public
    def executar(self, payload: ConsultaCreate) -> ConsultaResumo:
        """Executa uma consulta síncrona e grava resultados no banco + storage."""
        cliente = self.db.get(Cliente, payload.cliente_id)
        if cliente is None:
            raise ValueError(f"Cliente {payload.cliente_id} não encontrado")
        if not cliente.ativo:
            raise ValueError(f"Cliente {cliente.cnpj} está inativo")

        consulta = Consulta(
            cliente_id=cliente.id,
            tipo=payload.tipo,
            parametros=payload.parametros.model_dump(mode="json", exclude_none=True),
            status=StatusConsulta.processando,
            iniciado_em=datetime.utcnow(),
        )
        self.db.add(consulta)
        self.db.commit()
        self.db.refresh(consulta)

        inicio = time.perf_counter()
        novos_xmls = 0

        try:
            notas = self._chamar_giss(cliente, payload)
            consulta.total_notas = len(notas)
            consulta.total_paginas = max(1, (len(notas) + GISS_MAX_NOTAS_POR_PAGINA - 1) // GISS_MAX_NOTAS_POR_PAGINA)
            novos_xmls = self._persistir_notas(cliente, consulta, notas)
            consulta.status = StatusConsulta.sucesso
        except GISSException as e:
            consulta.status = StatusConsulta.erro
            consulta.erro_mensagem = str(e)
            logger.exception("Falha GISS na consulta %s", consulta.id)
        except Exception as e:  # pragma: no cover
            consulta.status = StatusConsulta.erro
            consulta.erro_mensagem = f"Erro inesperado: {e}"
            logger.exception("Erro inesperado na consulta %s", consulta.id)
        finally:
            consulta.finalizado_em = datetime.utcnow()
            consulta.duracao_ms = int((time.perf_counter() - inicio) * 1000)
            self.db.add(consulta)
            self.db.commit()
            self.db.refresh(consulta)

        return ConsultaResumo(
            consulta_id=consulta.id,
            status=consulta.status,
            total_notas=consulta.total_notas,
            total_paginas=consulta.total_paginas,
            duracao_ms=consulta.duracao_ms,
            erro_mensagem=consulta.erro_mensagem,
            novos_xmls=novos_xmls,
        )

    # ------------------------------------------------------------------ internal
    def _chamar_giss(self, cliente: Cliente, payload: ConsultaCreate) -> list[NfseData]:
        params = payload.parametros
        with build_client_for_cliente(cliente) as client:
            if payload.tipo == TipoConsulta.periodo_emissao:
                return client.consultar_todas_paginas(
                    "servico_prestado",
                    cnpj=cliente.cnpj,
                    inscricao_municipal=cliente.inscricao_municipal,
                    data_inicial=params.data_inicial,
                    data_final=params.data_final,
                    tipo_periodo="emissao",
                )
            if payload.tipo == TipoConsulta.periodo_competencia:
                return client.consultar_todas_paginas(
                    "servico_prestado",
                    cnpj=cliente.cnpj,
                    inscricao_municipal=cliente.inscricao_municipal,
                    data_inicial=params.data_inicial,
                    data_final=params.data_final,
                    tipo_periodo="competencia",
                )
            if payload.tipo == TipoConsulta.faixa:
                return client.consultar_todas_paginas(
                    "faixa",
                    cnpj=cliente.cnpj,
                    inscricao_municipal=cliente.inscricao_municipal,
                    nfse_inicial=params.nfse_inicial,
                    nfse_final=params.nfse_final,
                )
            if payload.tipo == TipoConsulta.rps:
                return client.consultar_todas_paginas(
                    "rps",
                    cnpj=cliente.cnpj,
                    inscricao_municipal=cliente.inscricao_municipal,
                    numero_rps=params.numero_rps,
                    serie_rps=params.serie_rps or "UNICA",
                    tipo_rps=params.tipo_rps or 1,
                )
        raise GISSException(f"Tipo de consulta não suportado: {payload.tipo}")

    def _persistir_notas(self, cliente: Cliente, consulta: Consulta, notas: list[NfseData]) -> int:
        novos = 0
        for nota in notas:
            if not nota.numero:
                continue

            # Dedup: mesma combinação (cliente + número) ou hash idêntico
            existente = (
                self.db.query(NfseXml)
                .filter(NfseXml.cliente_id == cliente.id, NfseXml.numero_nfse == nota.numero)
                .one_or_none()
            )
            xml_path, xml_hash = self.storage.save_xml(
                cnpj=cliente.cnpj,
                numero=nota.numero,
                competencia=nota.competencia,
                xml_content=nota.xml_completo,
            )
            if existente is not None:
                existente.xml_path = str(xml_path)
                existente.xml_hash = xml_hash
                existente.status_nfse = nota.status
                existente.consulta_id = consulta.id
                continue

            novo = NfseXml(
                cliente_id=cliente.id,
                consulta_id=consulta.id,
                numero_nfse=nota.numero,
                codigo_verificacao=nota.codigo_verificacao or None,
                data_emissao=nota.data_emissao,
                competencia=nota.competencia,
                valor_servicos=nota.valor_servicos,
                valor_iss=nota.valor_iss,
                valor_liquido=nota.valor_liquido,
                cnpj_prestador=nota.cnpj_prestador or None,
                cnpj_tomador=nota.cnpj_tomador,
                razao_social_tomador=nota.razao_social_tomador,
                item_lista_servico=nota.item_lista_servico or None,
                status_nfse=nota.status,
                xml_path=str(xml_path),
                xml_hash=xml_hash,
            )
            self.db.add(novo)
            novos += 1
        self.db.commit()
        return novos
