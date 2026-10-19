"""Punto de entrada de la aplicación FitLog / RunTracker.

Fase 0 — Inicialización de la aplicación.
Aplicación FastAPI mínima (standalone, sin dependencias de `core`) con un
health-check y un endpoint raíz. En fases posteriores se incorporan la
configuración (`core/config.py`), la base de datos y los routers de dominio.
"""

from fastapi import FastAPI

app = FastAPI(
    title="FitLog / RunTracker API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.get("/health", tags=["system"], summary="Health check")
def health() -> dict[str, str]:
    """Verifica que el servicio está arriba."""
    return {"status": "ok", "app": "FitLog / RunTracker API"}


@app.get("/", tags=["system"], summary="Root")
def root() -> dict[str, str]:
    """Punto de entrada informativo."""
    return {
        "name": "FitLog / RunTracker API",
        "version": "0.1.0",
        "docs": "/docs",
    }
