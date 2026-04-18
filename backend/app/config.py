"""Configurações da aplicação, carregadas a partir de variáveis de ambiente."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_name: str = "CUBO Captura"
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 8000

    # Database
    database_url: str = "sqlite:///./cubo_captura.db"

    # Storage
    storage_path: str = "./storage"
    cert_storage_path: str = "./storage/certificados"
    xml_storage_path: str = "./storage/xmls"

    # Security
    master_key: str = Field(default="change-me-dev-only-key-insecure-0123456789")
    allowed_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"])

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # GISS
    giss_wsdl_maceio: str = "https://ws-maceio.giss.com.br/service-ws/nf/nfse-ws?wsdl"
    giss_timeout_seconds: int = 60

    # Auth (JWT)
    jwt_secret: str = Field(default="change-me-jwt-secret-for-production-use")
    jwt_algorithm: str = "HS256"
    jwt_access_token_hours: int = 12

    # Admin inicial criado via seed (env vars). Deixar vazio para não criar.
    admin_email: str = ""
    admin_password: str = ""
    admin_nome: str = "Administrador"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    def ensure_directories(self) -> None:
        """Garante que os diretórios de storage existem."""
        for path in (self.storage_path, self.cert_storage_path, self.xml_storage_path):
            Path(path).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
