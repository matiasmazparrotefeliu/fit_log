"""Composition root de la API FitLog / RunTracker (Fase 2).

Monta la configuración (`settings`), los middlewares (CORS) y los routers de
dominio bajo `/api/v1`.
"""

from fastapi import APIRouter, FastAPI

from app.core.config import settings
from app.core.middleware import register_middlewares
from app.modules.auth.presentation.router import auth_router, users_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

register_middlewares(app)

# Router raíz de la API versionada.
api_v1_router = APIRouter(prefix=settings.api_v1_prefix)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
app.include_router(api_v1_router)


@app.get("/health", tags=["system"], summary="Health check")
def health() -> dict[str, str]:
    """Verifica que el servicio está arriba."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@app.get("/", tags=["system"], summary="Root")
def root() -> dict[str, str]:
    """Punto de entrada informativo."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "api": settings.api_v1_prefix,
    }
