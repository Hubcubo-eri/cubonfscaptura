"""Schemas Pydantic para Alertas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AlertaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tipo: str
    severity: str
    mensagem: str
    meta: Optional[dict[str, Any]] = None
    resolvido: bool
    resolvido_em: Optional[datetime] = None
    created_at: datetime
