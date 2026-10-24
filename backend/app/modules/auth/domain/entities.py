"""Entidades de dominio del módulo auth.

Lógica pura: sin FastAPI ni SQLAlchemy.
"""

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class UserRole(str, Enum):
    """Roles del sistema."""

    RUNNER = "runner"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


@dataclass
class User:
    """Usuario del sistema (atleta o administrador)."""

    id: uuid.UUID
    email: str
    password_hash: str
    full_name: str
    role: UserRole
    birth_date: date | None
    weight_kg: Decimal | None
    created_at: datetime
