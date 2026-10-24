"""Schemas Pydantic del módulo auth (Fase 2).

Todo payload de entrada y toda respuesta (incluidos errores) se manejan con
esquemas explícitos.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.auth.domain.entities import UserRole


class RegisterRequest(BaseModel):
    """Payload de registro público (siempre crea un runner)."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)
    birth_date: date | None = None
    weight_kg: Decimal | None = Field(default=None, ge=0, le=999.99)


class LoginRequest(BaseModel):
    """Credenciales de acceso."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Token JWT emitido al iniciar sesión."""

    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    """Representación pública de un usuario (sin password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    birth_date: date | None
    weight_kg: Decimal | None
    created_at: datetime


class UserUpdate(BaseModel):
    """Campos de perfil actualizables por el propio usuario."""

    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    birth_date: date | None = None
    weight_kg: Decimal | None = Field(default=None, ge=0, le=999.99)


class UserCreate(BaseModel):
    """Alta de usuario por parte de un super_admin."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)
    role: Literal["admin", "runner"] = "runner"
    birth_date: date | None = None
    weight_kg: Decimal | None = Field(default=None, ge=0, le=999.99)


class UserListResponse(BaseModel):
    """Página de usuarios."""

    items: list[UserRead]
    total: int
    page: int
    size: int
    pages: int


class ErrorResponse(BaseModel):
    """Formato uniforme de error de la API."""

    detail: str
