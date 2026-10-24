"""Casos de uso del módulo auth (Fase 2).

Orquestan el dominio y el puerto `UserRepository`. No conocen FastAPI.
"""

from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.application.dto import (
    CreateUserInput,
    LoginInput,
    RegisterUserInput,
    UpdateProfileInput,
)
from app.modules.auth.domain.entities import User, UserRole
from app.modules.auth.domain.errors import (
    EmailAlreadyExists,
    InvalidCredentials,
    InvalidRoleAssignment,
)
from app.modules.auth.domain.ports import UserRepository

# Roles que un super_admin puede crear por API (nunca super_admin).
_ASSIGNABLE_ROLES = {UserRole.ADMIN, UserRole.RUNNER}


class RegisterUser:
    """Registro público: siempre crea un `runner`."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def execute(self, data: RegisterUserInput) -> User:
        if self._repository.exists_by_email(data.email):
            raise EmailAlreadyExists(data.email)

        return self._repository.create(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole.RUNNER,
            birth_date=data.birth_date,
            weight_kg=data.weight_kg,
        )


class LoginUser:
    """Valida credenciales y emite un JWT."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def execute(self, data: LoginInput) -> tuple[User, str]:
        user = self._repository.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.password_hash):
            raise InvalidCredentials()

        token = create_access_token(subject=str(user.id), role=user.role.value)
        return user, token


class UpdateProfile:
    """Actualiza datos de perfil del propio usuario."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def execute(self, user: User, data: UpdateProfileInput) -> User:
        fields = {
            "full_name": data.full_name,
            "birth_date": data.birth_date,
            "weight_kg": data.weight_kg,
        }
        return self._repository.update(user, **fields)


class ListUsers:
    """Lista usuarios (solo super_admin)."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def execute(self, offset: int, limit: int) -> tuple[list[User], int]:
        return self._repository.list(offset=offset, limit=limit)


class CreateUser:
    """Crea un usuario con rol asignable (solo super_admin)."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def execute(self, data: CreateUserInput) -> User:
        if data.role not in _ASSIGNABLE_ROLES:
            raise InvalidRoleAssignment(data.role)
        if self._repository.exists_by_email(data.email):
            raise EmailAlreadyExists(data.email)

        return self._repository.create(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
            birth_date=data.birth_date,
            weight_kg=data.weight_kg,
        )
