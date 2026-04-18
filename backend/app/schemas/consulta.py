"""Schemas Pydantic para Consulta."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.consulta import StatusConsulta, TipoConsulta


class ConsultaParametros(BaseModel):
    """Parâmetros aceitos para uma consulta ao GISS."""

    data_inicial: Optional[date] = None
    data_final: Optional[date] = None
    nfse_inicial: Optional[int] = None
    nfse_final: Optional[int] = None
    numero_rps: Optional[int] = None
    serie_rps: Optional[str] = None
    tipo_rps: Optional[int] = None


class ConsultaCreate(BaseModel):
    cliente_id: str
    tipo: TipoConsulta
    parametros: ConsultaParametros

    @model_validator(mode="after")
    def validate_params(self) -> "ConsultaCreate":
        p = self.parametros
        if self.tipo in (TipoConsulta.periodo_emissao, TipoConsulta.periodo_competencia):
            if not p.data_inicial or not p.data_final:
                raise ValueError("data_inicial e data_final são obrigatórios para consulta por período")
            if p.data_inicial > p.data_final:
                raise ValueError("data_inicial deve ser anterior ou igual a data_final")
        elif self.tipo == TipoConsulta.faixa:
            if p.nfse_inicial is None or p.nfse_final is None:
                raise ValueError("nfse_inicial e nfse_final são obrigatórios para consulta por faixa")
            if p.nfse_inicial > p.nfse_final:
                raise ValueError("nfse_inicial deve ser menor ou igual a nfse_final")
        elif self.tipo == TipoConsulta.rps:
            if p.numero_rps is None:
                raise ValueError("numero_rps é obrigatório para consulta por RPS")
        return self


class ConsultaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cliente_id: str
    tipo: TipoConsulta
    parametros: Optional[dict[str, Any]]
    metodo_ws: Optional[str]
    status: StatusConsulta
    total_notas: int
    total_paginas: int
    erro_mensagem: Optional[str]
    duracao_ms: Optional[int]
    iniciado_em: Optional[datetime]
    finalizado_em: Optional[datetime]
    created_at: datetime


class ConsultaResumo(BaseModel):
    """Retorno sintético após disparar uma consulta."""

    consulta_id: str
    status: StatusConsulta
    total_notas: int
    total_paginas: int
    duracao_ms: Optional[int]
    erro_mensagem: Optional[str] = None
    novos_xmls: int = Field(default=0, description="XMLs novos salvos no storage")
