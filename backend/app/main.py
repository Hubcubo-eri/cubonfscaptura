"""FastAPI app entrypoint: CORS, lifespan, routers."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.database import init_db
from app.routers import agendamentos, clientes, consultas, dashboard, nfse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("cubo_captura")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Iniciando %s v%s [%s]", settings.app_name, __version__, settings.app_env)
    # create_all só em dev/SQLite; produção usa `alembic upgrade head`.
    if settings.database_url.startswith("sqlite") and settings.app_env != "production":
        init_db()
        logger.info("SQLite: schema sincronizado via create_all (sem Alembic)")
    yield
    logger.info("Encerrando %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Sistema de captura de XMLs NFS-e via Web Service GISS Maceió.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    app.include_router(clientes.router)
    app.include_router(consultas.router)
    app.include_router(nfse.router)
    app.include_router(dashboard.router)
    app.include_router(agendamentos.router)

    return app


app = create_app()
