"""Fixtures compartilhadas dos testes."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Permite rodar pytest da raiz do repositório ou de backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Força SQLite em memória + diretórios de storage temporários antes do import da app
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("MASTER_KEY", "test-master-key-do-not-use-in-prod-0123456789")
