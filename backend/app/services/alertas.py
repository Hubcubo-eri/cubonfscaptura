"""Serviço de alertas — hoje grava em log; futuro: webhook/e-mail/Slack."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger("cubo_captura.alertas")


class AlertaService:
    """Registra alertas operacionais (cert vencendo, falhas repetidas, etc.).

    Implementação inicial: log estruturado em JSON. Pode ser estendido para
    enviar a webhook/e-mail configurados em ``settings``.
    """

    @staticmethod
    def emitir(
        tipo: str,
        mensagem: str,
        metadata: Optional[dict[str, Any]] = None,
        severity: str = "warning",
    ) -> None:
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity": severity,
            "tipo": tipo,
            "mensagem": mensagem,
            "metadata": metadata or {},
        }
        # Log em uma única linha JSON para fácil ingestão por coletores.
        logger.warning("ALERTA %s", json.dumps(payload, ensure_ascii=False, default=str))
