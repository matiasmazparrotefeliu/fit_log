"""Utilidades de paginación (Fase 1).

Esquema genérico para listados de la API: parámetros de entrada
(`PageParams`) y una envoltura de respuesta (`Page`) con metadatos.
"""

from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    """Parámetros de paginación (query string)."""

    page: int = Field(default=1, ge=1, description="Número de página (1-based)")
    size: int = Field(default=20, ge=1, le=100, description="Elementos por página")

    @property
    def offset(self) -> int:
        """Desplazamiento para la consulta SQL."""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """Límite de filas a traer."""
        return self.size


class Page(BaseModel, Generic[T]):
    """Respuesta paginada genérica."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, params: PageParams) -> "Page[T]":
        """Construye una página calculando la cantidad total de páginas."""
        pages = ceil(total / params.size) if params.size else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )
