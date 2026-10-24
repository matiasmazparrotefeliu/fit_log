"""Dependencias de la capa presentation del módulo auth (Fase 2)."""

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import Principal, get_current_principal
from app.modules.auth.domain.entities import User
from app.modules.auth.domain.ports import UserRepository
from app.modules.auth.infrastructure.repository import SqlAlchemyUserRepository


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Provee un repositorio de usuarios ligado a la sesión del request."""
    return SqlAlchemyUserRepository(db)


def get_current_user(
    principal: Principal = Depends(get_current_principal),
    repository: UserRepository = Depends(get_user_repository),
) -> User:
    """Resuelve el usuario autenticado desde el JWT contra la base de datos."""
    try:
        user_id = uuid.UUID(principal.user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = repository.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
