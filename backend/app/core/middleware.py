"""Middlewares de la capa API/Gateway (Fase 2).

En esta fase se configura **solo CORS** a partir de `settings.cors_origins`.
El rate limiting se incorporará en una fase posterior (junto con `CachePort`).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


def register_middlewares(app: FastAPI) -> None:
    """Registra los middlewares transversales de la API."""
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
