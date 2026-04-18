"""FastAPI app entrypoint: CORS, lifespan, routers, auth guard."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.database import SessionLocal, init_db
from app.deps import get_current_user
from app.models import Usuario
from app.routers import agendamentos, alertas, auth, clientes, consultas, dashboard, nfse
from app.services.auth import hash_password

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("cubo_captura")


def _seed_admin() -> None:
    """Cria o admin inicial se ADMIN_EMAIL/ADMIN_PASSWORD estiverem definidos e não existir."""
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        return

    db = SessionLocal()
    try:
        existente = db.query(Usuario).filter(Usuario.email == settings.admin_email.lower()).one_or_none()
        if existente:
            return
        admin = Usuario(
            email=settings.admin_email.lower(),
            nome=settings.admin_nome,
            password_hash=hash_password(settings.admin_password),
            admin=True,
            ativo=True,
        )
        db.add(admin)
        db.commit()
        logger.info("Admin inicial criado: %s", settings.admin_email)
    except Exception:
        db.rollback()
        logger.exception("Falha ao criar admin inicial")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Iniciando %s v%s [%s]", settings.app_name, __version__, settings.app_env)
    if settings.database_url.startswith("sqlite") and settings.app_env != "production":
        init_db()
        logger.info("SQLite: schema sincronizado via create_all (sem Alembic)")
    _seed_admin()
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

    # Rotas abertas (sem auth)
    @app.get("/api/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    app.include_router(auth.router)  # /api/auth/login é público por natureza

    # Rotas protegidas por JWT
    protected = [Depends(get_current_user)]
    app.include_router(clientes.router, dependencies=protected)
    app.include_router(consultas.router, dependencies=protected)
    app.include_router(nfse.router, dependencies=protected)
    app.include_router(dashboard.router, dependencies=protected)
    app.include_router(agendamentos.router, dependencies=protected)
    app.include_router(alertas.router, dependencies=protected)

    return app


app = create_app()
