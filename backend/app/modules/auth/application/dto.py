"""DTOs de entrada/salida de los casos de uso (Fase 2).

Se usan `dataclass` (no Pydantic) para que la capa application no dependa
de frameworks de validación HTTP.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.modules.auth.domain.entities import UserRole


@dataclass(frozen=True)
class RegisterUserInput:
    email: str
    password: str
    full_name: str
    birth_date: date | None = None
    weight_kg: Decimal | None = None


@dataclass(frozen=True)
class LoginInput:
    email: str
    password: str


@dataclass(frozen=True)
class UpdateProfileInput:
    full_name: str | None = None
    birth_date: date | None = None
    weight_kg: Decimal | None = None


@dataclass(frozen=True)
class CreateUserInput:
    email: str
    password: str
    full_name: str
    role: UserRole
    birth_date: date | None = None
    weight_kg: Decimal | None = None
