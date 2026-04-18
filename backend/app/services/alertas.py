"""Serviço de alertas: persiste no banco + log estruturado.

Extensões futuras (fora do escopo do MVP):
- Envio a webhook Slack/Teams (campo ``settings.webhook_url``).
- Agrupamento (dedup) de alertas idênticos em janela de N horas.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Alerta

logger = logging.getLogger("cubo_captura.alertas")


class AlertaService:
    """Registra alertas operacionais (cert vencendo, falhas repetidas, etc.)."""

    @staticmethod
    def emitir(
        tipo: str,
        mensagem: str,
        metadata: Optional[dict[str, Any]] = None,
        severity: str = "warning",
        db: Optional[Session] = None,
    ) -> Optional[str]:
        """Persiste o alerta no banco e emite log JSON. Retorna o id do alerta."""
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity": severity,
            "tipo": tipo,
            "mensagem": mensagem,
            "metadata": metadata or {},
        }
        logger.warning("ALERTA %s", json.dumps(payload, ensure_ascii=False, default=str))

        session_owned = False
        if db is None:
            db = SessionLocal()
            session_owned = True

        try:
            alerta = Alerta(
                tipo=tipo,
                severity=severity,
                mensagem=mensagem,
                meta=metadata or {},
            )
            db.add(alerta)
            db.commit()
            db.refresh(alerta)
            return alerta.id
        except Exception:
            db.rollback()
            logger.exception("Falha ao persistir alerta")
            return None
        finally:
            if session_owned:
                db.close()
