"""Puertos (interfaces) del módulo auth.

`infrastructure` implementa estos contratos; `application` solo depende de ellos.
"""

import uuid
from typing import Protocol

from app.modules.auth.domain.entities import User, UserRole


class UserRepository(Protocol):
    """Contrato de persistencia para usuarios."""

    def get_by_email(self, email: str) -> User | None:
        """Busca un usuario por email."""
        ...

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Busca un usuario por id."""
        ...

    def exists_by_email(self, email: str) -> bool:
        """Indica si ya existe un usuario con ese email."""
        ...

    def create(
        self,
        *,
        email: str,
        password_hash: str,
        full_name: str,
        role: UserRole,
        birth_date,
        weight_kg,
    ) -> User:
        """Crea un usuario y lo persiste."""
        ...

    def update(self, user: User, **fields) -> User:
        """Actualiza campos de un usuario y lo persiste."""
        ...

    def list(self, offset: int, limit: int) -> tuple[list[User], int]:
        """Devuelve una página de usuarios y el total."""
        ...
